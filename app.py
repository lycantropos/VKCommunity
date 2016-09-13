import os

import requests
from vk_app import App, LoggingConfig
from vk_app.utils import get_raw_vk_objects_from_posts

from models import Photo
from settings import (GROUP_ID, APP_ID, USER_LOGIN, USER_PASSWORD, SCOPE,
                      DST_PATH, BASE_DIR, LOGGING_CONFIG_PATH, LOGS_PATH)


class CommunityApp(App):
    def __init__(self, app_id: int, group_id: str, user_login='', user_password='', scope='', access_token=None,
                 api_version='5.53'):
        super().__init__(app_id, user_login, user_password, scope, access_token, api_version)
        self.group_id = group_id
        self.logging_config = LoggingConfig(BASE_DIR, LOGGING_CONFIG_PATH, LOGS_PATH)
        self.logging_config.set()

    def load_community_wall_photos(self, params: dict) -> list:
        if 'owner_id' not in params:
            params['owner_id'] = '-' + self.group_id

        album_title = 'wall'

        community_wall_posts = self.get_items('wall.get', params)
        raw_photos = get_raw_vk_objects_from_posts(Photo, community_wall_posts)

        for raw_photo in raw_photos:
            raw_photo['album'] = album_title

        photos = Photo.get_vk_objects_from_raw(raw_photos)
        return photos

    def load_community_albums_photos(self, params: dict) -> list:
        if 'owner_id' not in params:
            params['owner_id'] = '-' + self.group_id

        albums = self.get_items('photos.getAlbums', params)

        photos = list()
        for album in albums:
            album_title = album['title']
            params['album_id'] = album['id']
            raw_photos = self.get_items('photos.get', params)
            for raw_photo in raw_photos:
                raw_photo['album'] = album_title
            album_photos = Photo.get_vk_objects_from_raw(raw_photos)
            photos += album_photos

        return photos

    def get_community_info(self, values: dict):
        community_info = self.api_session.groups.getById(**values)[0]
        return community_info

    @staticmethod
    def get_images_path(community_info: dict, base_dir=DST_PATH):
        community_screen_name = community_info['screen_name']
        images_path = os.path.join(base_dir, community_screen_name)
        return images_path

    def post_random_photos_on_wall(self, params: dict, num=1):
        if 'group_id' not in params:
            params['group_id'] = self.group_id

        group_id = params['group_id']

        values = dict(group_id=group_id)
        upload_server_url = self.get_upload_server_url(values)

        values = dict(
            group_id=group_id,
            fields='screen_name'
        )
        community_info = self.get_community_info(values)
        load_path = CommunityApp.get_images_path(community_info)

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

        values.update(response.json())

        response = self.api_session.photos.saveWallPhoto(**values)

        for ind, raw_photo in enumerate(response):
            photo = photos[ind]
            message = photo.comment + """
            #pic@hoboshelter
            #""" + photo.album.replace(' ', '_') + "@hoboshelter"
            values = dict(access_token=self.access_token, owner_id=raw_photo['owner_id'],
                          attachments='photo{}_{}'.format(raw_photo['owner_id'], raw_photo['id']),
                          message=message)
            self.api_session.wall.post(**values)

    def get_upload_server_url(self, values):
        response = self.api_session.photos.getWallUploadServer(**values)
        upload_server_url = response['upload_url']
        return upload_server_url


if __name__ == '__main__':
    community_app = CommunityApp(APP_ID, GROUP_ID, USER_LOGIN, USER_PASSWORD, SCOPE)
    community_app.load_community_albums_photos(dict())
