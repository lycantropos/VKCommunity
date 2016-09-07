from app import CommunityApp
from settings import GROUP_ID, APP_ID, USER_LOGIN, USER_PASSWORD, SCOPE

if __name__ == '__main__':
    community_app = CommunityApp(APP_ID, GROUP_ID, USER_LOGIN, USER_PASSWORD, SCOPE)
    params = dict()  # owner_id='-46521427' for "Brighton Beach"
    community_app.load_community_albums_photos(params)
