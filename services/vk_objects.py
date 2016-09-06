from datetime import datetime

from settings import DATE_FORMAT


def get_raw_vk_object_date(raw_vk_object: dict) -> str:
    raw_vk_object_date = datetime.fromtimestamp(raw_vk_object['date']).strftime(DATE_FORMAT)
    return raw_vk_object_date
