from datetime import datetime

from sqlalchemy import Column, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from vk_app.models import VKPhoto
from vk_app.utils import map_non_primary_columns_by_ancestor

Base = declarative_base()


class Photo(VKPhoto, Base):
    __tablename__ = 'photos'
    __table_args__ = {
        'mysql_charset': 'utf8'
    }

    vk_id = Column(String(255), primary_key=True)
    posted = Column(Boolean, default=False)


map_non_primary_columns_by_ancestor(ancestor=VKPhoto, inheritor=Photo)
