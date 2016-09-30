import os

import PIL.Image
import click

from app import CommunityApp
from models import Base
from services.data_access import DataAccessObject
from settings import DATABASE_URL
from settings import (DST_GROUP_ID, SRC_GROUP_ID, APP_ID, USER_LOGIN, USER_PASSWORD, SCOPE, RESTRICTED_ALBUMS,
                      DST_ABSPATH, WATERMARK_PATH)


@click.group(invoke_without_command=False)
def main():
    pass


@main.command(name='sync')
def sync():
    community_app = CommunityApp(APP_ID, DST_GROUP_ID, USER_LOGIN, USER_PASSWORD, SCOPE)
    images_path = os.path.join(DST_ABSPATH, community_app.community_info['screen_name'])
    watermark = PIL.Image.open(WATERMARK_PATH)
    community_app.synchronize_and_mark(images_path, watermark)


@main.command(name='post')
def post_bot():
    community_app = CommunityApp(APP_ID, DST_GROUP_ID, USER_LOGIN, USER_PASSWORD, SCOPE)
    images_path = os.path.join(DST_ABSPATH, community_app.community_info['screen_name'])
    filters = dict(
        owner_id='-{}'.format(SRC_GROUP_ID),
        restricted_albums=RESTRICTED_ALBUMS,
        marked=1,
    )
    community_app.post_random_photos_on_community_wall(filters, images_path)


@main.command(name='db')
def init_db():
    dao = DataAccessObject(DATABASE_URL)
    Base.metadata.create_all(dao.engine)


if __name__ == '__main__':
    main()
