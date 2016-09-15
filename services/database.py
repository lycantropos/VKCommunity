from typing import List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Photo
from settings import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True)
Session = sessionmaker(bind=engine)


def save_in_db(photos: List[Photo]):
    session = Session()
    try:
        for photo in photos:
            session.merge(photo)
        session.commit()
    finally:
        session.close()


def load_photos_from_db(session, filters: dict):
    q = session.query(Photo)

    owner_id = filters.get('owner_id', None)
    if owner_id:
        q = q.filter(
            Photo.owner_id == owner_id
        )

    album = filters.get('album', None)
    if owner_id:
        q = q.filter(
            Photo.album == album
        )

    start_time = filters.get('start_time', None)
    if start_time:
        q = q.filter(
            Photo.date_time >= start_time
        )
    end_time = filters.get('end_time', None)
    if end_time:
        q = q.filter(
            Photo.date_time <= end_time
        )

    photos = q.all()
    return photos
