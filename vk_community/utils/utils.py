from vk_app.utils import check_dir, get_year_month_date


def check_photos_year_month_dates_dir(photos: list, save_path: str):
    photos_year_month_dates = get_photos_year_month_dates(photos)
    for photos_year_month_date in photos_year_month_dates:
        check_dir(save_path, photos_year_month_date)


def get_photos_year_month_dates(photos: list) -> set:
    photos_year_month_dates = set(
        get_year_month_date(photo.post_date)
        for photo in photos
    )
    return photos_year_month_dates
