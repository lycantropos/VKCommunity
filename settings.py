import configparser
import os

CONFIGURATION_FILE_NAME = 'configuration.conf'
CURRENT_FILE_PATH = os.path.realpath(__file__)
CURRENT_FILE_ABSPATH = os.path.abspath(CURRENT_FILE_PATH)
CURRENT_FILE_DIR = os.path.dirname(CURRENT_FILE_ABSPATH)
CONFIGURATION_FILE_PATH = os.path.join(CURRENT_FILE_DIR, CONFIGURATION_FILE_NAME)
config = configparser.ConfigParser()
config.read(CONFIGURATION_FILE_PATH)

user = config['user']
USER_LOGIN = user.get('user_login')
USER_PASSWORD = user.get('user_password')

app = config['app']
APP_ID = app.get('app_id')
SCOPE = app.get('scope')
GROUP_ID = app.get('group_id')

files = config['files']
DST_PATH = files.get('dst_path')
SRC_PATH = files.get('src_path')

database = config['database']
DB_HOST = database.get('db_host')
DB_USER_NAME = database.get('db_user_name')
DB_USER_PASSWORD = database.get('db_user_password')
DB_NAME = database.get('db_name')

WATERMARK_DIR_PATH = os.path.join(os.getcwd(), 'utils')
WATERMARK_FILE_NAME = 'watermark.png'
WATERMARK_PATH = os.path.join(WATERMARK_DIR_PATH, WATERMARK_FILE_NAME)

# hyphen was chosen because its MySQL default DATE separator
DATE_SEP = '-'
DATE_ORDER = ['%Y', '%m', '%d']
DATE_FORMAT = DATE_SEP.join(DATE_ORDER)
