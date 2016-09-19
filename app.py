import logging
import os
from typing import List

import requests
from sqlalchemy.orm import sessionmaker
from vk_app import App
from vk_app.services.logging_config import LoggingConfig
from vk_app.services.vk_objects import get_vk_objects_from_raw, get_raw_vk_objects_from_posts
from vk_app.utils import check_dir

from models import Photo
from services.database import engine, save_in_db, load_photos_from_db
from settings import (SRC_GROUP_ID, APP_ID, USER_LOGIN, USER_PASSWORD, SCOPE,
                      DST_ABSPATH, BASE_DIR, LOGGING_CONFIG_PATH, LOGS_PATH)

MAX_ATTACHMENTS_LIMIT = 10
MAX_POSTS_PER_DAY = 50
POSTING_PERIOD_IN_SEC = 86400 / MAX_POSTS_PER_DAY


class CommunityApp(App):
    def __init__(self, app_id: int, group_id: str, user_login='', user_password='', scope='', access_token=None,
                 api_version='5.53'):
        super().__init__(app_id, user_login, user_password, scope, access_token, api_version)
        self.group_id = group_id
        self.db_session = sessionmaker(bind=engine)()
        self.logging_config = LoggingConfig(BASE_DIR, LOGGING_CONFIG_PATH, LOGS_PATH)
        self.logging_config.set()

    def synchronize(self):
        group_id = self.group_id
        values = dict(
            group_id=group_id,
            fields='screen_name'
        )
        community_info = self.get_community_info(values)
        path = CommunityApp.get_images_path(community_info)
        check_dir(path)
        params = dict()
        photos = self.load_community_albums_photos(params)
        save_in_db(self.db_session, photos)

        filters = dict()
        photos = load_photos_from_db(self.db_session, filters)
        for photo in photos:
            logging.info(photo)
            photo.synchronize(path)

    def load_community_wall_photos(self, params: dict) -> list:
        if 'owner_id' not in params:
            params['owner_id'] = '-{}'.format(self.group_id)

        album_title = 'wall'

        community_wall_posts = self.get_items('wall.get', params)
        raw_photos = get_raw_vk_objects_from_posts(Photo, community_wall_posts)

        for raw_photo in raw_photos:
            raw_photo['album'] = album_title

        photos = get_vk_objects_from_raw(Photo, raw_photos)
        return photos

    def load_community_albums_photos(self, params: dict) -> list:
        if 'owner_id' not in params:
            params['owner_id'] = '-{}'.format(self.group_id)

        albums = self.get_items('photos.getAlbums', params)

        photos = list()
        for album in albums:
            album_title = album['title']
            params['album_id'] = album['id']
            raw_photos = self.get_items('photos.get', params)
            for raw_photo in raw_photos:
                raw_photo['album'] = album_title
            album_photos = get_vk_objects_from_raw(Photo, raw_photos)
            photos += album_photos

        return photos

    def get_community_info(self, values: dict):
        community_info = self.api_session.groups.getById(**values)[0]
        return community_info

    @staticmethod
    def get_images_path(community_info: dict, path=DST_ABSPATH):
        community_screen_name = community_info['screen_name']
        images_path = os.path.join(path, community_screen_name)
        return images_path

    def post_photos_on_wall(self, photos: List[Photo], group_id: int):
        if not group_id:
            group_id = self.group_id

        values = dict(group_id=group_id)
        upload_server_url = self.get_upload_server_url(values)

        values = dict(
            group_id=self.group_id,
            fields='screen_name'
        )
        community_info = self.get_community_info(values)
        load_path = CommunityApp.get_images_path(community_info)

        if len(photos) > MAX_ATTACHMENTS_LIMIT:
            logging.warning(
                "Too many photos to post: {}, max available: {}".format(len(photos), MAX_ATTACHMENTS_LIMIT)
            )
            photos = photos[:MAX_ATTACHMENTS_LIMIT]

        marked_images_contents = list(
            photo.get_image_content(load_path, is_image_marked=True)
            for photo in photos
        )

        photos_files = list(
            ('file{}'.format(ind), ('pic.png', marked_image_content))
            for ind, marked_image_content in enumerate(marked_images_contents)
        )

        session = requests.Session()
        response = session.post(upload_server_url, files=photos_files)
        response = response.json()

        values = dict(group_id=group_id)
        values.update(response)

        response = self.api_session.photos.saveWallPhoto(**values)

        for ind, raw_photo in enumerate(response):
            photo = photos[ind]
            tags = ['pic', photo.album]
            message = photo.comment + ' '.join("#{}@{}".format(tag, community_info['screen_name']) for tag in tags)
            values = dict(access_token=self.access_token, owner_id='-{}'.format(group_id),
                          attachments='photo{}_{}'.format(raw_photo['owner_id'], raw_photo['id']),
                          message=message)
            self.api_session.wall.post(**values)
            self.db_session.query(Photo).filter_by(vk_id=photo.vk_id).update({'posted': True})
            self.db_session.commit()

    def get_upload_server_url(self, values):
        response = self.api_session.photos.getWallUploadServer(**values)
        upload_server_url = response['upload_url']
        return upload_server_url


if __name__ == '__main__':
    community_app = CommunityApp(APP_ID, SRC_GROUP_ID, USER_LOGIN, USER_PASSWORD, SCOPE)
    community_app.load_community_albums_photos(dict())
