from typing import List

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func

from models import Photo
from settings import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)


def save_in_db(session: Session, photos: List[Photo]):
    for photo in photos:
        session.merge(photo)
    session.commit()


def load_photos_from_db(session: Session, filters: dict):
    q = session.query(Photo)

    owner_id = filters.get('owner_id', None)
    if owner_id:
        q = q.filter(
            Photo.owner_id == owner_id
        )

    albums = filters.get('albums', None)
    if albums:
        q = q.filter(
            Photo.album.in_(albums)
        )
    restricted_albums = filters.get('restricted_albums', None)
    if restricted_albums:
        q = q.filter(
            Photo.album.notin_(restricted_albums)
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

    posted = filters.get('posted', False)
    q = q.filter(
        Photo.posted.is_(posted)
    )

    random = filters.get('random', None)
    if random:
        q = q.order_by(func.rand())

    limit = filters.get('limit', None)
    if limit:
        q = q.limit(limit)

    offset = filters.get('offset', None)
    if offset:
        q = q.offset(offset)

    photos = q.all()
    return photos
