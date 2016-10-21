import calendar
import datetime
import unittest

from sqlalchemy.engine.url import make_url
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy_utils import drop_database
from vk_community.models import Photo
from vk_community.services.data_access import check_filters, DataAccessObject


class IntegrationTestsDataAccess(unittest.TestCase):
    def setUp(self):
        self.dao_url = make_url('sqlite:///community_app.db')
        if not database_exists(self.dao_url):
            create_database(self.dao_url)
        self.dao = DataAccessObject(self.dao_url)
        self.photos = [
            Photo(owner_id=-129836227, object_id=431928280, album_id=-7, album='wall',
                  date_time=datetime.datetime(2016, 9, 30, 23, 55, 7), user_id=100, text=None,
                  link='http://cs638122.vk.me/v638122248/1c41/SnfoaFP-Hfk.jpg')
        ]

    def tearDown(self):
        drop_database(self.dao_url)

    def test_save_photos(self):
        if not self.dao.engine.dialect.has_table(self.dao.engine, Photo.__tablename__):
            Photo.__table__.create(bind=self.dao.engine)
        self.dao.save_photos(self.photos)
        photos = self.dao.session.query(Photo).all()
        self.assertListEqual(photos, self.photos)


class UnitTestsDataAccess(unittest.TestCase):
    def setUp(self):
        self.raw_filters = dict(
            owner_id='-14',
            albums=['wall', 'graffiti'],
            restricted_albums=['saved'],
            start_datetime=717728719,
            end_datetime=5832683395,
            posted='1',
            marked='0',
            random='1',
            limit='100',
            offset='10'
        )
        self.filters = dict(
            owner_id=-14,
            albums=['wall', 'graffiti'],
            restricted_albums=['saved'],
            start_datetime=datetime.datetime(1992, 9, 29, 1, 5, 19),
            end_datetime=datetime.datetime(2154, 10, 30, 21, 49, 55),
            posted=True,
            marked=False,
            random=True,
            limit=100,
            offset=10
        )

    def test_check_filters(self):
        check_filters(self.raw_filters)
        self.assertDictEqual(self.raw_filters, self.filters)


class UnitTestsExceptionsDataAccess(unittest.TestCase):
    def test_check_filters_bad_int_parameters(self):
        # owner id may be integer or string representing integer with hyphen for negative values, dash is not an option
        self.assertRaises(ValueError, check_filters, dict(owner_id='–14'))
        # classic example with typos like 1-l, o-0
        self.assertRaises(ValueError, check_filters, dict(limit='l40'))
        self.assertRaises(ValueError, check_filters, dict(offset='1o'))

    def test_check_filters_bad_list_parameters(self):
        self.assertRaises(TypeError, check_filters, dict(albums='wall,graffiti'))
        self.assertRaises(TypeError, check_filters, dict(restricted_albums='saved'))

    def test_check_filters_bad_bool_parameters(self):
        self.assertRaises(ValueError, check_filters, dict(posted=-1))
        self.assertRaises(ValueError, check_filters, dict(marked='-1'))
        self.assertRaises(ValueError, check_filters, dict(random='l'))

    def test_check_filters_bad_datetime_parameters(self):
        self.assertRaises(
            ValueError, check_filters, dict(start_datetime=calendar.timegm(datetime.datetime.max.utctimetuple()) + 1)
        )
        self.assertRaises(
            ValueError, check_filters, dict(start_datetime=calendar.timegm(datetime.datetime.min.utctimetuple()) - 1)
        )
        self.assertRaises(TypeError, check_filters, dict(start_datetime='2154-10-30 21:49:55'))
