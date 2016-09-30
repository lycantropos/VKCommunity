import logging
import os
from datetime import datetime
from typing import List

import PIL.Image
import requests
from vk_app import App
from vk_app.services.logging_config import LoggingConfig
from vk_app.services.vk_objects import get_raw_vk_objects_from_posts
from vk_app.utils import check_dir, CallRepeater

from models import Photo
from services.data_access import check_filters, DataAccessObject
from services.images import mark_images
from settings import (BASE_DIR, LOGGING_CONFIG_PATH, LOGS_PATH, DATABASE_URL, SRC_GROUP_ID)

MAX_ATTACHMENTS_LIMIT = 10
MAX_POSTS_PER_DAY = 50
DAY_IN_SEC = 86400
POSTING_PERIOD_IN_SEC = DAY_IN_SEC / MAX_POSTS_PER_DAY


class CommunityApp(App):
    def __init__(self, app_id: int, group_id: str, user_login='', user_password='', scope='', access_token=None,
                 api_version='5.53'):
        super().__init__(app_id, user_login, user_password, scope, access_token, api_version)
        self.group_id = group_id
        self.community_info = self.api_session.groups.getById(group_id=self.group_id, fields='screen_name')[0]
        self.data_access_object = DataAccessObject(DATABASE_URL)
        self.logging_config = LoggingConfig(BASE_DIR, LOGGING_CONFIG_PATH, LOGS_PATH)
        self.logging_config.set()

    @CallRepeater.make_periodic(DAY_IN_SEC)
    def synchronize_and_mark(self, images_path: str, watermark: PIL.Image.Image):
        params = dict(owner_id='-{}'.format(SRC_GROUP_ID))
        photos = self.load_albums_photos(params)
        self.data_access_object.save_photos(photos)
        self.synchronize_files(images_path)
        mark_images(images_path, watermark)

    # TODO: write this to remove posts which are earlier than earliest of posted photos
    # and to unset posted for photos which are later than latest of posts
    def synchronize_posts(self):
        filters = dict()
        photos = self.data_access_object.load_photos(filters)
        params = dict()
        community_wall_posts = self.load_wall_posts(params)

    def synchronize_files(self, images_path: str):
        filters = dict()
        photos = self.data_access_object.load_photos(filters)
        photos.sort(
            key=lambda x: (x.album, int(x.date_time.strftime("%s")), x.link)
        )

        files_paths = list(
            os.path.join(root, file)
            for root, dirs, files in os.walk(images_path)
            for file in files
            if file.endswith('.jpg')
        )
        check_dir(images_path)
        for photo in photos:
            logging.info(photo)
            photo.synchronize(images_path, files_paths)

    def load_wall_photos(self, params: dict) -> list:
        community_wall_posts = self.load_wall_posts(params)
        raw_photos = get_raw_vk_objects_from_posts(Photo, community_wall_posts)

        for raw_photo in raw_photos:
            raw_photo['album'] = 'wall'

        photos = list(
            Photo.from_raw(raw_photo)
            for raw_photo in raw_photos
        )
        return photos

    def load_wall_posts(self, params: dict):
        if 'owner_id' not in params:
            params['owner_id'] = '-{}'.format(self.group_id)

        wall_posts = self.get_items('wall.get', params)
        return wall_posts

    def load_albums_photos(self, params: dict) -> list:
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
            album_photos = list(
                Photo.from_raw(raw_photo)
                for raw_photo in raw_photos
            )

            photos += album_photos

        return photos

    @CallRepeater.make_periodic(POSTING_PERIOD_IN_SEC)
    def post_random_photos_on_community_wall(self, filters: dict, images_path: str):
        check_filters(filters)
        filters['random'] = True
        filters['limit'] = filters.get('limit', 1)
        filters['posted'] = False
        random_photos = self.data_access_object.load_photos(filters)
        self.post_photos_on_community_wall(random_photos, images_path=images_path, marked=filters.get('marked', False))

    def post_photos_on_community_wall(self, photos: List[Photo], images_path: str, marked=False):
        if len(photos) > MAX_ATTACHMENTS_LIMIT:
            logging.warning(
                "Too many photos to post: {}, max available: {}".format(len(photos), MAX_ATTACHMENTS_LIMIT)
            )
            photos = photos[:MAX_ATTACHMENTS_LIMIT]

        images_contents = list(
            photo.get_image_content(images_path, marked=marked)
            for photo in photos
        )

        photos_files = list(
            ('file{}'.format(ind), ('pic.png', marked_image_content))
            for ind, marked_image_content in enumerate(images_contents)
        )

        values = dict(group_id=self.group_id)
        response = self.api_session.photos.getWallUploadServer(**values)
        upload_server_url = response['upload_url']
        with requests.Session() as session:
            response = session.post(upload_server_url, files=photos_files)
            values.update(response.json())

        response = self.api_session.photos.saveWallPhoto(**values)

        for ind, raw_photo in enumerate(response):
            photo = photos[ind]
            tags = ['pic', photo.album.replace(' ', '_')]
            message = '\n'.join([
                photo.comment, '\n'.join('#{}@{}'.format(tag, self.community_info['screen_name']) for tag in tags)
            ])
            self.api_session.wall.post(
                access_token=self.access_token,
                owner_id='-{}'.format(self.group_id),
                attachments='photo{}_{}'.format(raw_photo['owner_id'], raw_photo['id']),
                message=message
            )
            photo.posted = True
            photo.date_time = datetime.utcnow()
        self.data_access_object.save_photos(photos)
