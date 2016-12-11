import datetime
import logging
import os
from collections import defaultdict
from typing import List, Callable, Dict

import PIL.Image
from vk_app import App
from vk_app.models.attachables import VKAttachable
from vk_app.utils import check_dir
from vk_community.models import Photo, Post
from vk_community.services.data_access import DataAccessObject, check_filters
from vk_community.services.images import mark_images

MAX_ATTACHMENTS_LIMIT = 10


def download_attachments(attachments, reload_path, **kwargs):
    unloaded_attachments = list()
    for attachment in attachments:
        for key, attachable in attachment.items():
            try:
                attachable.download(reload_path, **kwargs)
            except AttributeError:
                logging.exception('Can\'t download attachment of type: "{}"'
                                  .format(type(attachable)))
                unloaded_attachments.append({key: attachable})
    return unloaded_attachments


class CommunityApp(App):
    def __init__(self, app_id: int = 0, group_id: int = 1, user_login: str = '', user_password: str = '',
                 scope: str = '', access_token: str = None, api_version: str = '5.57',
                 dao: DataAccessObject = DataAccessObject('sqlite:///community_app.db')):
        super().__init__(app_id, user_login, user_password, scope, access_token, api_version)
        self.group_id = group_id
        self.community_info = self.api_session.groups.getById(group_id=self.group_id,
                                                              fields='screen_name')[0]
        self.dao = dao

    def synchronize_and_mark(self, images_path: str, src: str, watermark: PIL.Image.Image,
                             **params):
        self.synchronize(images_path, src, **params)
        mark_images(images_path, watermark)

    def synchronize(self, images_path: str, src: str, **params):
        """
        :param images_path: path to directory containing images
        :param src: source of community photos.
        Ex.: src="wall"
        would correspond to photos from wall posts.

        Allowable values: "wall", "album", "all"
        """
        self.synchronize_dao(src, **params)
        self.synchronize_files(images_path)

    def synchronize_dao(self, src: str, **params):
        if src == 'album':
            photos = self.load_albums_photos(**params)
        elif src == 'wall':
            photos = self.load_wall_photos(**params)
        elif src == 'all':
            photos = self.load_albums_photos(**params)
            photos += self.load_wall_photos(**params)
        else:
            err_description = ('Incorrect `src` value: {src}\n'
                               'Allowable values: "wall", "album", "all".').format(src=src)
            raise ValueError(err_description)
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
        params.setdefault('owner_id', -self.group_id)
        filters = dict(posted=1)
        check_filters(filters)
        posted_photos = self.dao.load_photos(**filters)
        if posted_photos:
            posted_photos.sort(key=lambda x: (x.date_time, x.object_id), reverse=True)
            first_posted_photo_date = posted_photos[-1].date_time
            posts = self.load_posts(**params)
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

    def load_wall_photos(self, **params):
        posts = self.load_posts(**params)
        photos = list(
            attachable
            for post in posts
            for attachment in post.attachments
            for key, attachable in attachment.items()
            if key == Photo.key()
        )
        return photos

    def load_posts(self, **params) -> List[Post]:
        params.setdefault('owner_id', -self.group_id)

        raw_posts = self.get_all_objects('wall.get', **params)
        posts = list(
            Post.from_raw(raw_post)
            for raw_post in raw_posts
        )
        return posts

    def delete_wall_post(self, wall_post: Post):
        for attachment in wall_post.attachments:
            for key, vk_attachment in attachment:
                params = {'owner_id': vk_attachment.owner_id,
                          '{}_id'.format(key): vk_attachment.object_id}
                self.api_session.__call__('{}.delete'.format(key), **params)
        values = dict(owner_id=wall_post.owner_id, post_id=wall_post.object_id)
        self.api_session.wall.delete(**values)

    def load_albums_photos(self, **params) -> List[Photo]:
        params.setdefault('owner_id', -self.group_id)

        albums = self.get_all_objects('photos.getAlbums', **params)

        photos = list()
        for album in albums:
            album_title = album['title']
            params['album_id'] = album['id']
            raw_photos = self.get_all_objects('photos.get', **params)
            album_photos = list(
                Photo.from_raw(raw_photo)
                for raw_photo in raw_photos
            )
            for album_photo in album_photos:
                album_photo.album = album_title

            photos += album_photos

        return photos

    def duplicate_post(self, post: Post, reload_path: str = None,
                       editor: Callable[[str], str] = lambda x: x,
                       **params) -> str:
        post.text = editor(post.text)

        if reload_path is not None:
            post.attachments = self.reload_attachments(post.attachments,
                                                       reload_path=reload_path,
                                                       **params)

        post_id = self.post_on_wall(post, **params)
        return post_id

    def post_on_wall(self, post: Post, **params) -> str:
        """Returns id of post"""
        params.setdefault('owner_id', -self.group_id)
        params.setdefault('from_group', 1)
        message = post.text
        attachments = ','.join(
            '{key}{vk_id}'.format(key=key, vk_id=content.vk_id)
            for attachment in post.attachments
            for key, content in attachment.items()
        )
        response = self.api_session.wall.post(message=message,
                                              attachments=attachments,
                                              **params)
        return response['post_id']

    def reload_attachments(self, attachments: List[Dict[str, VKAttachable]],
                           reload_path: str, **kwargs) -> List[Dict[str, VKAttachable]]:
        reloaded_attachments = download_attachments(attachments, reload_path, **kwargs)

        attachables_files = defaultdict(list)
        for ind, attachment in enumerate(attachments):
            if attachment in reloaded_attachments:
                continue
            for attachable in attachment.values():
                file_path = attachable.get_file_path(reload_path)
                file_name = ''.join([attachable.key(), str(ind), attachable.get_file_extension()])
                with open(file_path, mode='rb') as file:
                    attachables_files[attachable.__class__].append(
                        (
                            'file',
                            (file_name, file.read())
                        )
                    )

        for attachable_type, files in attachables_files.items():
            get_upload_server_method = attachable_type.identify_getUploadServer_method(dst_type='wall')
            upload_url = self.get_upload_server_url(
                get_upload_server_method, group_id=self.group_id
            )

            save_method = attachable_type.identify_save_method(dst_type='wall')
            response = list(
                self.upload_files_on_vk_server(
                    save_method, upload_url, files=[file],
                    group_id=self.group_id,
                )
                for file in files
            )

            vk_attachables = list()
            for raw_vk_attachment in response:
                if isinstance(raw_vk_attachment, list):
                    raw_vk_attachment, = raw_vk_attachment
                vk_attachables.append(
                    attachable_type.from_raw(raw_vk_attachment)
                )

            reloaded_attachments.extend(
                list({vk_attachable.key(): vk_attachable}
                     for vk_attachable in vk_attachables)
            )

        ordered_new_attachments = list()
        for attachment in attachments:
            due_attachment = next(
                new_attachment
                for new_attachment in reloaded_attachments
                if new_attachment.keys() == attachment.keys()
            )
            reloaded_attachments.remove(due_attachment)
            ordered_new_attachments.append(due_attachment)
        return ordered_new_attachments

    def post_random_photos_on_community_wall(self, images_path: str, **filters: dict):
        check_filters(filters)
        filters['random'] = True
        filters['limit'] = filters.get('limit', 1)
        filters['posted'] = False
        random_photos = self.dao.load_photos(**filters)
        self.post_photos_on_community_wall(random_photos, images_path=images_path,
                                           marked=filters.get('marked', False))

    def post_photos_on_community_wall(self, photos: List[Photo], images_path: str,
                                      marked=False):
        if len(photos) > MAX_ATTACHMENTS_LIMIT:
            logging.warning(
                "Too many photos to post: {count}, "
                "max available: {limit}".format(count=len(photos),
                                                limit=MAX_ATTACHMENTS_LIMIT)
            )
            photos = photos[:MAX_ATTACHMENTS_LIMIT]

        params = dict(group_id=self.group_id)
        upload_url = self.get_upload_server_url('photos.getWallUploadServer', **params)

        images_contents = list(
            photo.get_file_content(images_path, marked=marked)
            for photo in photos
        )
        pic_tag = 'pic'
        image_name = ''.join([pic_tag,
                              Photo.MARKED_FILE_EXTENSION if marked else Photo.FILE_EXTENSION])
        images = list(
            ('file{}'.format(ind), (image_name, image_content))
            for ind, image_content in enumerate(images_contents)
        )

        raw_photos = self.upload_files_on_vk_server('photos.saveWallPhoto', upload_url, images,
                                                    **params)

        for ind, raw_photo in enumerate(raw_photos):
            photo = photos[ind]
            tags = [pic_tag, photo.album.replace(' ', '_')]
            message = '\n'.join([
                photo.text or '',
                '\n'.join('#{}@{}'.format(tag, self.community_info['screen_name'])
                          for tag in tags)
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
            photo.date_time = datetime.datetime.utcnow()
        self.dao.save_photos(photos)
