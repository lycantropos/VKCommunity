from datetime import datetime
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import func

from models import Photo
from settings import DATETIME_FORMAT


class DataAccessObject:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, echo=False)
        self.session = sessionmaker(bind=self.engine)()

    def __del__(self):
        self.session.close()

    def save_photos(self, photos: List[Photo]):
        for photo in photos:
            self.session.merge(photo)
        self.session.commit()

    def load_photos(self, **filters) -> List[Photo]:
        q = self.session.query(Photo)

        owner_id = filters.get('owner_id')
        if owner_id is not None:
            q = q.filter(
                Photo.owner_id == owner_id
            )

        albums = filters.get('albums')
        if albums is not None:
            q = q.filter(
                Photo.album.in_(albums)
            )
        restricted_albums = filters.get('restricted_albums')
        if restricted_albums is not None:
            q = q.filter(
                Photo.album.notin_(restricted_albums)
            )

        start_datetime = filters.get('start_datetime')
        if start_datetime is not None:
            q = q.filter(
                Photo.date_time >= start_datetime
            )
        end_datetime = filters.get('end_datetime')
        if end_datetime is not None:
            q = q.filter(
                Photo.date_time <= end_datetime
            )

        posted = filters.get('posted')
        if posted is not None:
            q = q.filter(
                Photo.posted.is_(posted)
            )

        random = filters.get('random')
        if random is not None:
            q = q.order_by(func.rand())

        limit = filters.get('limit')
        if limit is not None:
            q = q.limit(limit)

        offset = filters.get('offset')
        if offset is not None:
            q = q.offset(offset)

        photos = q.all()
        return photos


def check_filters(filters):
    owner_id = filters.get('owner_id')
    if owner_id is not None:
        filters['owner_id'] = int(owner_id)

    albums = filters.get('albums')
    if albums is not None:
        albums[:] = albums
    restricted_albums = filters.get('restricted_albums')
    if restricted_albums is not None:
        restricted_albums[:] = restricted_albums

    start_datetime = filters.get('start_datetime')
    if start_datetime is not None:
        filters['start_datetime'] = datetime.utcfromtimestamp(start_datetime)
    end_datetime = filters.get('end_datetime')
    if end_datetime is not None:
        filters['end_datetime'] = datetime.utcfromtimestamp(end_datetime)

    posted = filters.get('posted')
    if posted is not None:
        posted = int(posted)
        if posted not in [0, 1]:
            raise ValueError("'posted' filter parameter should be `bool` type value or "
                             "`int` type value from range {0, 1}")
        filters['posted'] = posted == 1

    marked = filters.get('marked')
    if marked is not None:
        marked = int(marked)
        if marked not in [0, 1]:
            raise ValueError("'marked' filter parameter should be `bool` type value or "
                             "`int` type value from range {0, 1}")
        filters['marked'] = marked == 1

    random = filters.get('random')
    if random is not None:
        random = int(random)
        if random not in [0, 1]:
            raise ValueError("'random' filter parameter should be `bool` type value or "
                             "`int` type value from range {0, 1}")
        filters['random'] = random == 1

    limit = filters.get('limit')
    if limit is not None:
        filters['limit'] = int(limit)

    offset = filters.get('offset')
    if offset is not None:
        filters['offset'] = int(offset)
