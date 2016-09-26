import re
from datetime import datetime
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import func

from models import Photo


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

    def load_photos(self, filters: dict) -> List[Photo]:
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

        start_time = filters.get('start_time')
        if start_time is not None:
            q = q.filter(
                Photo.date_time >= start_time
            )
        end_time = filters.get('end_time')
        if end_time is not None:
            q = q.filter(
                Photo.date_time <= end_time
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


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

OWNER_ID_RE = r'^(-?\d+$)$'


def check_filters(filters: dict):
    owner_id = filters.get('owner_id')
    if owner_id is not None:
        filters['owner_id'] = re.match(OWNER_ID_RE, owner_id).group(1)

    albums = filters.get('albums')
    if albums is not None:
        albums[:] = albums
    restricted_albums = filters.get('restricted_albums')
    if restricted_albums is not None:
        restricted_albums[:] = restricted_albums

    start_time = filters.get('start_time')
    if start_time is not None:
        filters['start_time'] = datetime.strptime(start_time, DATETIME_FORMAT)
    end_time = filters.get('end_time')
    if end_time is not None:
        filters['end_time'] = datetime.strptime(end_time, DATETIME_FORMAT)

    posted = filters.get('posted')
    if posted is not None:
        filters['random'] = int(posted) == 1

    marked = filters.get('marked')
    if marked is not None:
        filters['marked'] = int(marked) == 1

    random = filters.get('random')
    if random is not None:
        filters['random'] = int(random) == 1

    limit = filters.get('limit')
    if limit is not None:
        filters['offset'] = int(limit)

    offset = filters.get('offset')
    if offset is not None:
        filters['offset'] = int(offset)
