import datetime
import os
import unittest

from sqlalchemy.engine.url import make_url
from sqlalchemy_utils import create_database
from sqlalchemy_utils import database_exists
from sqlalchemy_utils import drop_database

from vk_community.app import CommunityApp
from vk_community.models import Photo
from vk_community.services.data_access import DataAccessObject


class IntegrationTestsApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dao_url = make_url('sqlite:///community_app.db')
        if not database_exists(cls.dao_url):
            create_database(cls.dao_url)
        cls.app = CommunityApp(dao=DataAccessObject(cls.dao_url))

        cls.path = os.path.dirname(__file__)
        cls.test_files = list(
            os.path.join(root, file)
            for root, _, files in os.walk(cls.path)
            for file in files
        )
        cls.test_drs = list(
            os.path.join(root, dr)
            for root, drs, _ in os.walk(cls.path)
            for dr in drs
        )

    @classmethod
    def tearDownClass(cls):
        drop_database(cls.dao_url)
        files = list(
            os.path.join(root, file)
            for root, _, files in os.walk(cls.path)
            for file in files
        )
        for file in files:
            if file not in cls.test_files:
                os.remove(file)

        drs = list(
            os.path.join(root, dr)
            for root, drs, _ in os.walk(cls.path)
            for dr in drs
        )
        # `os.rmdir` removes only empty directories, so we need start deleting from inner subdirectories
        # which have longer abspath
        drs.sort(key=lambda dr: len(dr), reverse=True)
        for dr in drs:
            if dr not in cls.test_drs:
                os.rmdir(dr)

    def setUp(self):
        Photo.__table__.create(bind=self.app.dao.engine)
        self.photos = [
            Photo(owner_id=-129836227, object_id=431928280, album_id=-7, album='wall',
                  date_time=datetime.datetime(2016, 9, 30, 23, 55, 7), user_id=100, comment=None,
                  link='http://cs638122.vk.me/v638122248/1c41/SnfoaFP-Hfk.jpg')
        ]

    def tearDown(self):
        Photo.__table__.drop(bind=self.app.dao.engine)

    def test_vk_api_photos_getById(self):
        photos_ids = ','.join(p.vk_id for p in self.photos)
        photos = list(
            Photo.from_raw(raw_photo)
            for raw_photo in self.app.api_session.photos.getById(photos=photos_ids)
        )
        self.assertEqual(photos, self.photos)

    def test_save_photos(self):
        self.app.dao.save_photos(self.photos)
        photos = self.app.dao.load_photos()
        self.assertListEqual(photos, self.photos)

    def test_synchronize_files(self):
        old_photos_paths = list(
            photo.get_file_path(self.path)
            for photo in self.photos
        )
        self.app.dao.save_photos(self.photos)
        self.app.synchronize_files(self.path)
        self.assertTrue(all(os.path.exists(old_photo_path) for old_photo_path in old_photos_paths))

        for photo in self.photos:
            photo.album = photo.album[::-1] or 'test'
        new_photos_paths = list(
            photo.get_file_path(self.path)
            for photo in self.photos
        )
        self.assertTrue(all(not os.path.exists(new_photo_path) for new_photo_path in new_photos_paths))
        self.app.dao.save_photos(self.photos)
        self.app.synchronize_files(self.path)
        self.assertTrue(all(not os.path.exists(old_photo_path) for old_photo_path in old_photos_paths))
        self.assertTrue(all(os.path.exists(new_photo_path) for new_photo_path in new_photos_paths))


if __name__ == '__main__':
    unittest.main()
