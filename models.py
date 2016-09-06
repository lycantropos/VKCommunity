import os

from utils import get_year_month_date, get_valid_folders
from utils.utils import download


class Photo:
    def __init__(self, vk_id: int, owner_id: int, user_id: int, album: str,
                 link: str, text: str, post_date: str):
        self.vk_id = vk_id
        self.owner_id = owner_id
        self.user_id = user_id
        self.album = album
        self.link = link
        self.text = text
        self.post_date = post_date

    def get_image_path(self, save_path: str) -> str:
        photo_album = self.album
        photo_date = self.post_date
        image_name = self.get_image_name()
        year_month_date = get_year_month_date(photo_date)
        image_subfolders = get_valid_folders(photo_album, year_month_date, image_name)
        image_path = os.path.join(save_path, *image_subfolders)
        return image_path

    def get_image_name(self) -> str:
        photo_url = self.link
        image_name = photo_url.split('/')[-1]
        return image_name

    def download(self, save_path: str):
        photo_link = self.link
        image_path = self.get_image_path(save_path)

        download(photo_link, image_path)

    def get_image_content(self, images_path: str, is_image_marked=True) -> bytearray:
        image_path = self.get_image_path(images_path)
        if is_image_marked:
            image_path = image_path.replace('.jpg', '.png')
        with open(image_path, 'rb') as marked_image:
            image_content = marked_image.read()
            return image_content

    def __str__(self):
        return self.link
