from typing import List

from sqlalchemy.orm import sessionmaker

from models import Photo, engine

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
        q.filter(
            Photo.owner_id == owner_id
        )

    start_time = filters.get('start_time', None)
    if start_time:
        q.filter(
            Photo.date_time >= start_time
        )
    end_time = filters.get('end_time', None)
    if end_time:
        q.filter(
            Photo.date_time <= end_time
        )

    photos = q.all()
    return photos
