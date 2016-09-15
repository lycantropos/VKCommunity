import os
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from vk_app import VKObject
from vk_app.utils import get_year_month_date, get_valid_dirs, download, check_dir

from settings import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True)
connection = engine.connect()
Base = declarative_base()


class Photo(Base, VKObject):
    __tablename__ = 'photo'
    __table_args__ = {
        'mysql_charset': 'utf8'
    }

    vk_id = Column(Integer, primary_key=True, autoincrement=False)
    owner_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)

    album = Column(String(255), nullable=False)
    comment = Column(String(255), nullable=True)

    date_time = Column(DateTime, nullable=False)
    link = Column(String(255), unique=True)

    def __init__(self, vk_id: int, owner_id: int, user_id: int, album: str, comment: str, date_time: datetime,
                 link: str):
        # VK utility fields
        self.vk_id = vk_id
        self.owner_id = owner_id
        self.user_id = user_id

        # info fields
        self.album = album
        self.comment = comment

        # technical info fields
        self.date_time = date_time
        self.link = link

    def __repr__(self):
        return "<Photo(album='{}', link='{}', date_time='{}')>".format(
            self.album, self.link, self.date_time
        )

    def __str__(self):
        return "Photo from '{}' album".format(self.album)

    @classmethod
    def name(cls):
        return 'photo'

    @classmethod
    def info_fields(cls):
        return [
            'album',
            'comment'
        ]

    def download(self, path: str):
        image_subdirs = self.get_file_subdirs()
        check_dir(path, *image_subdirs)

        image_dir = os.path.join(path, *image_subdirs)
        image_name = self.get_file_name()
        image_path = os.path.join(image_dir, image_name)

        download(self.link, image_path)

    def get_file_subdirs(self) -> list:
        year_month_date = get_year_month_date(self.date_time)
        image_subdirs = get_valid_dirs(self.album, year_month_date)
        return image_subdirs

    def get_file_name(self) -> str:
        image_name = self.link.split('/')[-1]
        return image_name

    def get_image_content(self, path: str, is_image_marked=True) -> bytearray:
        image_subdirs = self.get_file_subdirs()
        image_dir = os.path.join(path, *image_subdirs)

        image_name = self.get_file_name()
        if is_image_marked:
            image_name = image_name.replace('.jpg', '.png')

        image_path = os.path.join(image_dir, image_name)
        with open(image_path, 'rb') as marked_image:
            image_content = marked_image.read()
            return image_content

    @classmethod
    def from_raw(cls, raw_photo: dict):
        return Photo(
            int(raw_photo['id']), int(raw_photo['owner_id']), int(raw_photo.pop('user_id', 0)),
            raw_photo['album'], raw_photo['text'], datetime.fromtimestamp(raw_photo['date']),
            Photo.get_link(raw_photo)
        )

    @staticmethod
    def get_link(raw_photo: dict) -> str:
        photo_link_key_prefix = 'photo_'

        photo_link_keys = list(
            raw_photo_key
            for raw_photo_key in raw_photo
            if photo_link_key_prefix in raw_photo_key
        )
        photo_link_keys.sort(key=lambda x: int(x.replace(photo_link_key_prefix, '')))

        highest_res_link_key = photo_link_keys[-1]
        highest_res_link = raw_photo[highest_res_link_key]

        return highest_res_link
