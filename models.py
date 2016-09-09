import os
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from vk_app import VKObject
from vk_app.utils import get_year_month_date, get_valid_folders, download

from settings import DATABASE_URI

engine = create_engine(DATABASE_URI)
connection = engine.connect()
Base = declarative_base()


class Photo(VKObject):
    __tablename__ = 'photos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    vk_id = Column(Integer, primary_key=True, autoincrement=False)
    owner_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)

    album = Column(String(255), nullable=False)
    text = Column(String(255), nullable=True)
    link = Column(String(255), primary_key=True)

    post_date = Column(DateTime, nullable=False)

    def __init__(self, vk_id: int, owner_id: int, user_id: int, album: str, text: str, link: str,
                 post_date: datetime, is_posted=False):
        self.vk_id = vk_id
        self.owner_id = owner_id
        self.user_id = user_id
        self.album = album
        self.link = link
        self.text = text
        self.post_date = post_date
        self.is_posted = is_posted

    def __repr__(self):
        return "<Photo(album='{}', link='{}', post_date='{}')>".format(
            self.album, self.link, self.post_date
        )

    def __str__(self):
        return "Photo from '{}' album".format(self.album)

    def download(self, save_path: str):
        photo_link = self.link
        image_path = self.get_image_path(save_path)

        download(photo_link, image_path)

    def get_image_path(self, save_path: str) -> str:
        photo_album_title = self.album
        photo_date = self.post_date
        image_name = self.get_image_name()
        year_month_date = get_year_month_date(photo_date)
        image_subfolders = get_valid_folders(photo_album_title, year_month_date, image_name)
        image_path = os.path.join(save_path, *image_subfolders)
        return image_path

    def get_image_name(self) -> str:
        photo_url = self.link
        image_name = photo_url.split('/')[-1]
        return image_name

    def get_image_content(self, images_path: str, is_image_marked=True) -> bytearray:
        image_path = self.get_image_path(images_path)
        if is_image_marked:
            image_path = image_path.replace('.jpg', '.png')
        with open(image_path, 'rb') as marked_image:
            image_content = marked_image.read()
            return image_content

    @classmethod
    def from_raw(cls, raw_photo: dict):
        return Photo(int(raw_photo['id']), int(raw_photo['owner_id']), int(raw_photo.pop('user_id', 0)),
                     raw_photo['album'], raw_photo['text'], Photo.get_link_to_highest_resolution(raw_photo),
                     datetime.fromtimestamp(raw_photo['date']))

    @staticmethod
    def get_link_to_highest_resolution(raw_photo: dict) -> str:
        raw_photo_link_key_prefix = 'photo_'

        raw_photo_link_keys = list(
            raw_photo_key
            for raw_photo_key in raw_photo
            if raw_photo_link_key_prefix in raw_photo_key
        )
        raw_photo_link_keys.sort(key=lambda x: int(x.replace(raw_photo_link_key_prefix, '')))

        highest_resolution_raw_photo_link_key = raw_photo_link_keys[-1]
        highest_resolution_raw_photo_link = raw_photo[highest_resolution_raw_photo_link_key]

        return highest_resolution_raw_photo_link
