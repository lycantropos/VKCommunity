import typing

from mutagen import File, id3
from selenium.webdriver.remote.webdriver import WebDriver
from sqlalchemy import Column, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from vk_app.attachables import VKPhoto, VKAudio, VKAttachable
from vk_app.post import VKPost
from vk_app.utils import map_non_primary_columns_by_ancestor, get_year_month_date, get_valid_dirs, get_all_subclasses
from vk_community.services.lyrics import load_lyrics_from_musixmatch, load_lyrics_from_wikia, load_lyrics_from_azlyrics

Base = declarative_base()


class Photo(VKPhoto, Base):
    __tablename__ = 'photos'
    __table_args__ = {
        'mysql_charset': 'utf8'
    }

    vk_id = Column(String(255), primary_key=True)
    posted = Column(Boolean, default=False)

    def get_file_subdirs(self) -> typing.List[str]:
        year_month_date = get_year_month_date(self.date_time)
        image_subdirs = get_valid_dirs(self.album, year_month_date)
        return image_subdirs


class Audio(VKAudio, Base):
    __tablename__ = 'meta'
    __table_args__ = {
        'mysql_charset': 'utf8'
    }

    vk_id = Column(String(255), primary_key=True)

    def download(self, path: str, web_driver: WebDriver = None, service_url: str = '',
                 lyrics='', website='', comment=''):
        file_path = super().download(path)
        try:
            meta = id3.ID3(file_path)
        except id3.ID3NoHeaderError:
            meta = File(file_path)
            meta.add_tags()

        if web_driver:
            lyrics = self.load_lyrics(web_driver)
        meta['TPE1'] = id3._frames.TPE1(text=[self.artist])
        meta['TIT2'] = id3._frames.TIT2(text=[self.title])
        meta['USLT'] = id3._frames.USLT(text=lyrics)
        meta['WORS'] = id3._frames.WORS(text=[website])
        meta['COMM'] = id3._frames.COMM(text=[comment])
        meta.save()
        return file_path

    def load_lyrics(self, web_driver: WebDriver) -> str:
        lyrics = load_lyrics_from_wikia(self.artist, self.title, web_driver) or \
                 load_lyrics_from_azlyrics(self.artist, self.title, web_driver) or \
                 load_lyrics_from_musixmatch(self.artist, self.title, web_driver)
        return lyrics


map_non_primary_columns_by_ancestor(ancestor=VKPhoto, inheritor=Photo)
map_non_primary_columns_by_ancestor(ancestor=VKAudio, inheritor=Audio)


class Post(VKPost):
    VK_ATTACHABLE_BY_KEY = dict(
        (inheritor.key(), inheritor)
        for inheritor in get_all_subclasses(VKAttachable)
        if inheritor.key() is not None
    )
