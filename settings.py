import configparser
import os

from sqlalchemy.engine import url

CONFIGURATION_FILE_NAME = 'configuration.conf'
CURRENT_FILE_PATH = os.path.realpath(__file__)
CURRENT_FILE_ABSPATH = os.path.abspath(CURRENT_FILE_PATH)
BASE_DIR = os.path.dirname(CURRENT_FILE_ABSPATH)
CONFIGURATION_FILE_FOLDER = 'configurations'
CONFIGURATION_FILE_PATH = os.path.join(BASE_DIR, CONFIGURATION_FILE_FOLDER, CONFIGURATION_FILE_NAME)
config = configparser.ConfigParser()
config.read(CONFIGURATION_FILE_PATH)

user = config['user']
USER_LOGIN = user.get('user_login')
USER_PASSWORD = user.get('user_password')
ACCESS_TOKEN = user.get('access_token')

app = config['app']
APP_ID = int(app.get('app_id'))
SCOPE = app.get('scope')
SRC_GROUP_ID = int(app.get('src_group_id'))
DST_GROUP_ID = int(app.get('dst_group_id'))
FORBIDDEN_ALBUMS = app.get('forbidden_albums').split(',')

files = config['files']
DST_ABSPATH = files.get('dst_abspath')

database = config['database']
DATABASE_URL = url.make_url(database['database_url'])

logger = config['logger']
LOGS_PATH = logger.get('logs_path')
LOGGING_CONFIG_PATH = logger.get('logging_config_path')

formatting = config['formatting']
DATETIME_FORMAT = formatting.get('datetime_format')

WATERMARK_DIR_PATH = os.path.join(BASE_DIR, 'utils')
WATERMARK_FILE_NAME = 'watermark.png'
WATERMARK_PATH = os.path.join(WATERMARK_DIR_PATH, WATERMARK_FILE_NAME)
