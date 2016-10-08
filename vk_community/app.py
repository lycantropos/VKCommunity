import logging
import os
from datetime import datetime
from typing import List

import PIL.Image
import requests
from vk_app import App
from vk_app.models.post import VKPost
from vk_app.utils import check_dir, CallRepeater, CallDelayer

from vk_community.models import Photo
from vk_community.services.data_access import check_filters, DataAccessObject
from vk_community.services.images import mark_images

MAX_ATTACHMENTS_LIMIT = 10
MAX_POSTS_PER_DAY = 50
DAY_IN_SEC = 86400
POSTING_PERIOD_IN_SEC = DAY_IN_SEC / MAX_POSTS_PER_DAY
MINIMAL_INTERVAL_BETWEEN_DELETE_REQUESTS_IN_SECONDS = 1.7


class CommunityApp(App):
    def __init__(self, app_id: int = 0, group_id: int = 1, user_login: str = '', user_password: str = '',
                 scope: str = '', access_token: str = None, api_version: str = '5.57',
                 dao: DataAccessObject = DataAccessObject('sqlite:///community_app.db')):
        super().__init__(app_id, user_login, user_password, scope, access_token, api_version)
        self.group_id = group_id
        self.community_info = self.api_session.groups.getById(group_id=self.group_id, fields='screen_name')[0]
        self.dao = dao

    @CallRepeater.make_periodic(DAY_IN_SEC)
    def synchronize_and_mark(self, images_path: str, watermark: PIL.Image.Image, **params):
        self.synchronize(images_path, **params)
        mark_images(images_path, watermark)

    def synchronize(self, images_path: str, **params):
        self.synchronize_dao(params)
        self.synchronize_files(images_path)

    def synchronize_dao(self, params):
        photos = self.load_albums_photos(**params)
        self.dao.save_photos(photos)

    def synchronize_files(self, path: str):
        photos = self.dao.load_photos()

        files_paths = list(
            os.path.join(root, file)
            for root, dirs, files in os.walk(path)
            for file in files
            if file.endswith('.jpg')
        )
        check_dir(path)
        for photo in photos:
            logging.info(photo)
            photo.synchronize(path, files_paths)

    def synchronize_wall_posts(self, **params):
        if 'owner_id' not in params:
            params['owner_id'] = -self.group_id
        filters = dict(posted=1)
        check_filters(filters)
        posted_photos = self.dao.load_photos(**filters)
        if posted_photos:
            posted_photos.sort(key=lambda x: (x.date_time, x.object_id), reverse=True)
            first_posted_photo_date = posted_photos[-1].date_time
            posts = self.load_wall_posts(params)
            posts.sort(key=lambda x: (x.date_time, x.object_id))
            posts_for_delete = list()
            for ind, post in enumerate(posts):
                if post.date_time < first_posted_photo_date:
                    posts_for_delete.append(post)
                else:
                    break
            for post_for_delete in posts_for_delete:
                self.delete_wall_post(post_for_delete)
            last_post_date = posts[-1].date_time
            unposted_photos = list()
            for ind, posted_photo in enumerate(posted_photos):
                if posted_photo.date_time > last_post_date:
                    posted_photo.posted = False
                    unposted_photos.append(posted_photo)
                else:
                    break
            self.dao.save_photos(unposted_photos)

    def load_wall_posts(self, params: dict) -> List[VKPost]:
        if 'owner_id' not in params:
            params['owner_id'] = -self.group_id

        raw_wall_posts = self.get_items('wall.get', **params)
        wall_posts = list(
            VKPost.from_raw(raw_wall_post)
            for raw_wall_post in raw_wall_posts
        )
        return wall_posts

    @CallDelayer.make_delayed(MINIMAL_INTERVAL_BETWEEN_DELETE_REQUESTS_IN_SECONDS)
    def delete_wall_post(self, wall_post: VKPost):
        values = dict(owner_id=wall_post.owner_id, post_id=wall_post.object_id)
        self.api_session.wall.delete(**values)

    def load_albums_photos(self, **params) -> List[Photo]:
        if 'owner_id' not in params:
            params['owner_id'] = -self.group_id

        albums = self.get_items('photos.getAlbums', **params)

        photos = list()
        for album in albums:
            album_title = album['title']
            params['album_id'] = album['id']
            raw_photos = self.get_items('photos.get', **params)
            album_photos = list(
                Photo.from_raw(raw_photo)
                for raw_photo in raw_photos
            )
            for album_photo in album_photos:
                album_photo.album = album_title

            photos += album_photos

        return photos

    @CallRepeater.make_periodic(POSTING_PERIOD_IN_SEC)
    def post_random_photos_on_community_wall(self, images_path: str, **filters: dict):
        check_filters(filters)
        filters['random'] = True
        filters['limit'] = filters.get('limit', 1)
        filters['posted'] = False
        random_photos = self.dao.load_photos(**filters)
        self.post_photos_on_community_wall(random_photos, images_path=images_path, marked=filters.get('marked', False))

    def post_photos_on_community_wall(self, photos: List[Photo], images_path: str, marked=False):
        if len(photos) > MAX_ATTACHMENTS_LIMIT:
            logging.warning(
                "Too many photos to post: {}, max available: {}".format(len(photos), MAX_ATTACHMENTS_LIMIT)
            )
            photos = photos[:MAX_ATTACHMENTS_LIMIT]

        values = dict(group_id=self.group_id)
        response = self.api_session.photos.getWallUploadServer(**values)
        upload_server_url = response['upload_url']

        images_contents = list(
            photo.get_image_content(images_path, marked=marked)
            for photo in photos
        )
        pic_tag = 'pic'
        image_name = pic_tag + Photo.MARKED_FILE_EXTENSION if marked else pic_tag + Photo.FILE_EXTENSION
        images = list(
            ('file{}'.format(ind), (image_name, image_content))
            for ind, image_content in enumerate(images_contents)
        )
        with requests.Session() as session:
            response = session.post(upload_server_url, files=images)
            values.update(response.json())

        response = self.api_session.photos.saveWallPhoto(**values)

        for ind, raw_photo in enumerate(response):
            photo = photos[ind]
            tags = [pic_tag, photo.album.replace(' ', '_')]
            message = '\n'.join([
                photo.comment, '\n'.join('#{}@{}'.format(tag, self.community_info['screen_name']) for tag in tags)
            ])
            self.api_session.wall.post(
                access_token=self.access_token,
                owner_id=-self.group_id,
                attachments='{key}{owner_id}_{object_id}'.format(
                    key=Photo.key(), owner_id=raw_photo['owner_id'], object_id=raw_photo['id']
                ),
                message=message
            )
            photo.posted = True
            photo.date_time = datetime.utcnow()
        self.dao.save_photos(photos)
