import os
import threading
from urllib.request import urlopen

from settings import MYSQL_DATE_SEP


def find_file(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)
    return None


def check_dir(folder_path: str, *subfolders):
    full_path = os.path.join(folder_path, *subfolders)
    if not os.path.exists(full_path):
        os.mkdir(full_path)


def download(link: str, save_path: str):
    if not os.path.exists(save_path):
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


def get_year_month_date(date: str, sep='.') -> str:
    year_month_date = sep.join(date.split(MYSQL_DATE_SEP)[:-1])
    return year_month_date


def get_valid_folders(*folders) -> list:
    valid_folders = filter(None, folders)
    valid_folders = list(valid_folders)
    return valid_folders
