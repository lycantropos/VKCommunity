import logging
import shutil
from datetime import datetime
from time import sleep

import MySQLdb as Mdb

from models import Photo
from services.database import (INNER_PHOTOS_TABLE_INSERT_REQUEST, INNER_PHOTOS_TABLE_UPDATE_REQUEST,
                               OUTER_PHOTOS_TABLE_UPDATE_REQUEST, OUTER_PHOTOS_TABLE_INSERT_REQUEST)
from settings import DB_HOST, DB_USER_NAME, DB_USER_PASSWORD, DB_NAME
from utils import find_file, DATE_FORMAT, check_dir, get_year_month_date


def download_photos(photos: list, save_path: str):
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


def synchronize_photos_with_photos_table(photos: list, save_path: str, is_inner_photos_table: bool):
    con = Mdb.connect(DB_HOST, DB_USER_NAME, DB_USER_PASSWORD, DB_NAME, charset="utf8")
    if is_inner_photos_table:
        photos_table_update_request = INNER_PHOTOS_TABLE_UPDATE_REQUEST
        photos_table_insert_request = INNER_PHOTOS_TABLE_INSERT_REQUEST
    else:
        photos_table_update_request = OUTER_PHOTOS_TABLE_UPDATE_REQUEST
        photos_table_insert_request = OUTER_PHOTOS_TABLE_INSERT_REQUEST

    with con:
        cur = con.cursor()
        for photo in photos:
            image_path = photo.get_image_path(save_path)
            image_name = photo.get_image_name()
            old_image_path = find_file(image_name, save_path)
            if old_image_path:
                shutil.move(old_image_path, image_path)
                req = photos_table_update_request.format(**photo.__dict__)
            else:
                req = photos_table_insert_request.format(**photo.__dict__)

            cur.execute(req)


def get_raw_photos(posts: list) -> list:
    raw_photos = list(
        attachment['photo']
        for post in posts
        if 'attachments' in post
        for attachment in post['attachments']
        if 'photo' in attachment
    )
    return raw_photos


def get_photos_from_raw(raw_photos: list, album_title: str) -> list:
    photos = list(
        Photo(
            int(raw_photo['id']), int(raw_photo['owner_id']),
            int(raw_photo.pop('user_id', 0)), album_title,
            get_highest_resolution_raw_photo_link(raw_photo),
            raw_photo['text'],
            get_raw_photo_date(raw_photo)
        )
        for raw_photo in raw_photos
    )
    return photos


def get_highest_resolution_raw_photo_link(raw_photo: dict) -> str:
    raw_photo_link_keys = get_raw_photo_link_keys(raw_photo)
    raw_photo_link_keys.sort(key=lambda x: int(x.replace('photo_', '')))
    highest_resolution_raw_photo_link_key = raw_photo_link_keys[-1]
    highest_resolution_raw_photo_link = raw_photo[highest_resolution_raw_photo_link_key]
    return highest_resolution_raw_photo_link


RAW_PHOTO_LINK_KEY_PREFIX = 'photo_'


def get_raw_photo_link_keys(raw_photo: dict) -> list:
    raw_photo_link_keys = list(
        raw_photo_key
        for raw_photo_key in raw_photo
        if RAW_PHOTO_LINK_KEY_PREFIX in raw_photo_key
    )
    return raw_photo_link_keys


def get_raw_photo_date(raw_photo: dict) -> str:
    raw_photo_date = datetime.fromtimestamp(raw_photo['date']).strftime(DATE_FORMAT)
    return raw_photo_date


def get_photos_year_month_dates(photos: list) -> set:
    photos_year_month_dates = set(
        get_year_month_date(photo.post_date)
        for photo in photos
    )
    return photos_year_month_dates


def check_photos_year_month_dates_dir(photos: list, save_path: str):
    photos_year_month_dates = get_photos_year_month_dates(photos)
    for photos_year_month_date in photos_year_month_dates:
        check_dir(save_path, photos_year_month_date)
