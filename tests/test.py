from vk_app.utils import check_dir

from app import CommunityApp
from services.database import save_in_db
from settings import GROUP_ID, APP_ID, USER_LOGIN, USER_PASSWORD, SCOPE

if __name__ == '__main__':
    community_app = CommunityApp(APP_ID, GROUP_ID, USER_LOGIN, USER_PASSWORD, SCOPE)
    params = dict()
    photos = community_app.load_community_albums_photos(params)
    save_in_db(photos)
    group_id = community_app.group_id

    values = dict(
        group_id=group_id,
        fields='screen_name'
    )
    community_info = community_app.get_community_info(values)

    save_path = CommunityApp.get_images_path(community_info)
    check_dir(save_path)
