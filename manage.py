import os
import unittest

import PIL.Image
import click

from app import CommunityApp
from models import Base
from services.data_access import DataAccessObject
from settings import DATABASE_URL
from settings import (DST_GROUP_ID, SRC_GROUP_ID, APP_ID, USER_LOGIN, USER_PASSWORD, SCOPE, FORBIDDEN_ALBUMS,
                      DST_ABSPATH, WATERMARK_PATH)
from tests.test_data_access import UnitTestDataAccess, UnitTestDataAccessExceptions


@click.group(name='run', invoke_without_command=False)
def run():
    pass


@run.command(name='run_sync')
def sync():
    community_app = CommunityApp(APP_ID, DST_GROUP_ID, USER_LOGIN, USER_PASSWORD, SCOPE)
    images_path = os.path.join(DST_ABSPATH, community_app.community_info['screen_name'])
    watermark = PIL.Image.open(WATERMARK_PATH)
    community_app.synchronize_and_mark(images_path, watermark)


@run.command(name='run_bot')
def post_bot():
    community_app = CommunityApp(APP_ID, DST_GROUP_ID, USER_LOGIN, USER_PASSWORD, SCOPE)
    images_path = os.path.join(DST_ABSPATH, community_app.community_info['screen_name'])
    filters = dict(
        owner_id=-SRC_GROUP_ID,
        forbidden_albums=FORBIDDEN_ALBUMS,
        marked=1,
    )
    community_app.post_random_photos_on_community_wall(images_path, **filters)


@run.command(name='run_db')
def init_db():
    dao = DataAccessObject(DATABASE_URL)
    Base.metadata.create_all(dao.engine)


@click.group(name='test', invoke_without_command=False)
def test():
    pass


@test.command(name='test_dao')
def test_data_access():
    """Tests implemented data access"""
    suite = unittest.TestLoader().loadTestsFromTestCase(UnitTestDataAccess)
    unittest.TextTestRunner(verbosity=2).run(suite)
    exc_suite = unittest.TestLoader().loadTestsFromTestCase(UnitTestDataAccessExceptions)
    unittest.TextTestRunner(verbosity=2).run(exc_suite)

manage = click.CommandCollection(sources=[run, test])

if __name__ == '__main__':
    manage()
