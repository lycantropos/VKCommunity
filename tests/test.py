import logging

from app import CommunityApp
from settings import GROUP_ID, APP_ID, USER_LOGIN, USER_PASSWORD, SCOPE

logging.basicConfig(
    format='%(name)-12s: %(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
    level=logging.INFO,
    filename='vk_processing.log', filemode='w'
)
logger_vk = logging.getLogger(__name__)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger().addHandler(console)

if __name__ == '__main__':
    community_app = CommunityApp(GROUP_ID, APP_ID, USER_LOGIN, USER_PASSWORD, SCOPE)
    params = dict(owner_id='-46521427')
    community_app.load_community_wall_photos(params)
