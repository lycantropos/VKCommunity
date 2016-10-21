from typing import List

from sqlalchemy import Column, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from vk_app.attachables import VKPhoto
from vk_app.utils import map_non_primary_columns_by_ancestor, get_year_month_date, get_valid_dirs

Base = declarative_base()


class Photo(VKPhoto, Base):
    __tablename__ = 'photos'
    __table_args__ = {
        'mysql_charset': 'utf8'
    }

    vk_id = Column(String(255), primary_key=True)
    posted = Column(Boolean, default=False)

    def get_file_subdirs(self) -> List[str]:
        year_month_date = get_year_month_date(self.date_time)
        image_subdirs = get_valid_dirs(self.album, year_month_date)
        return image_subdirs


map_non_primary_columns_by_ancestor(ancestor=VKPhoto, inheritor=Photo)
