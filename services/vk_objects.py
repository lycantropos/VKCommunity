import logging
from datetime import datetime
from time import sleep


def download_vk_objects(photos: list, save_path: str):
    last_download_time = datetime.utcnow()
    for photo in photos:
        try:
            # we can send request to VK servers only 3 times a second
            time_elapsed_since_last_download = (datetime.utcnow() - last_download_time).total_seconds()
            if time_elapsed_since_last_download < 0.33:
                sleep(0.33 - time_elapsed_since_last_download)
            last_download_time = datetime.utcnow()

            photo.download(save_path)
        except OSError as e:
            # e.g. raises when there is no photo on the server anymore
            logging.info(photo)
            logging.exception(e)


def get_raw_objects_from_posts(posts: list, object_name: str) -> list:
    raw_photos = list(
        attachment[object_name]
        for post in posts
        if 'attachments' in post
        for attachment in post['attachments']
        if object_name in attachment
    )
    return raw_photos
