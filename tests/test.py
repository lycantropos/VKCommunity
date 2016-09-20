from app import CommunityApp
from services.database import load_photos_from_db
from services.images import mark_images
from settings import SRC_GROUP_ID, APP_ID, USER_LOGIN, USER_PASSWORD, SCOPE, RESTRICTED_ALBUMS, DST_GROUP_ID, \
    DST_ABSPATH, WATERMARK_PATH, SRC_ABSPATH

if __name__ == '__main__':
    community_app = CommunityApp(APP_ID, SRC_GROUP_ID, USER_LOGIN, USER_PASSWORD, SCOPE)
    community_app.synchronize(path=DST_ABSPATH)
    path = SRC_ABSPATH
    mark_images(path, WATERMARK_PATH)
    try:
        filters = dict(
            owner_id='-{}'.format(SRC_GROUP_ID),
            restricted_albums=RESTRICTED_ALBUMS,
            random=True,
            limit=1
        )
        random_photos = load_photos_from_db(community_app.db_session, filters)
        community_app.post_photos_on_wall(random_photos, group_id=DST_GROUP_ID, path=path)
    finally:
        community_app.db_session.close()
