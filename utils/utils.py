import os
import threading
from datetime import datetime
from time import sleep
from urllib.request import urlopen


def find_file(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)
    return None


def check_dir(folder_path: str, *subfolders):
    full_path = os.path.join(folder_path, *subfolders)
    if not os.path.exists(full_path):
        os.mkdir(full_path)


LAST_DOWNLOAD_TIME = datetime.utcnow()


def download(link: str, save_path: str):
    if not os.path.exists(save_path):
        global LAST_DOWNLOAD_TIME
        time_elapsed_since_last_download = (datetime.utcnow() - LAST_DOWNLOAD_TIME).total_seconds()
        if time_elapsed_since_last_download < 0.3:
            sleep(0.3 - time_elapsed_since_last_download)
        LAST_DOWNLOAD_TIME = datetime.utcnow()
        response = urlopen(link)
        if response.status == 200:
            with open(save_path, 'wb') as out:
                image_content = response.read()
                out.write(image_content)


def make_periodic(delay: int):
    def launch_periodically(function):
        def launched_periodically(*args, **kwargs):
            timer = threading.Timer(delay, function, args=args, kwargs=kwargs)
            try:
                timer.start()
            except RuntimeError:
                timer.cancel()
                launched_periodically(*args, **kwargs)

        return launched_periodically

    return launch_periodically


MYSQL_DATE_SEP = '-'
MYSQL_DATE_ORDER = ['%Y', '%m', '%d']
DATE_FORMAT = MYSQL_DATE_SEP.join(MYSQL_DATE_ORDER)


def get_year_month_date(date: str, sep='.') -> str:
    year_month_date = sep.join(date.split(MYSQL_DATE_SEP)[:-1])
    return year_month_date


def get_valid_folders(*folders) -> list:
    valid_folders = filter(None, folders)
    valid_folders = list(valid_folders)
    return valid_folders
