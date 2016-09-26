import configparser
import os
from urllib.parse import quote_plus

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
RESTRICTED_ALBUMS = app.get('restricted_albums').split(',')

files = config['files']
DST_ABSPATH = files.get('dst_abspath')

database = config['database']
DB_HOST = database.get('db_host')
DB_USER_NAME = database.get('db_user_name')
DB_USER_PASSWORD = quote_plus(database.get('db_user_password'))
DB_NAME = database.get('db_name')

DATABASE_URL = url.URL(
    drivername='mysql',
    host=DB_HOST,
    port=3306,
    username=DB_USER_NAME,
    password=DB_USER_PASSWORD,
    database=DB_NAME,
    query={'charset': 'utf8mb4'}
)

logger = config['logger']
LOGS_PATH = logger.get('logs_path')
LOGGING_CONFIG_PATH = logger.get('logging_config_path')

formatting = config['formatting']
DATETIME_FORMAT = formatting.get('datetime_format')

WATERMARK_DIR_PATH = os.path.join(BASE_DIR, 'utils')
WATERMARK_FILE_NAME = 'watermark.png'
WATERMARK_PATH = os.path.join(WATERMARK_DIR_PATH, WATERMARK_FILE_NAME)
