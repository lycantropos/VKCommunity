from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import Insert

from models import Photo, engine


@compiles(Insert)
def append_string(insert, compiler, **kw):
    s = compiler.visit_insert(insert, **kw)
    if 'mysql_append_string' in insert.kwargs:
        return s + " " + insert.kwargs['mysql_append_string']
    return s


Insert.argument_for("mysql", "append_string", None)

Session = sessionmaker(bind=engine)


def save_in_db(audios: list):
    audios_dicts = list(audio.as_dict() for audio in audios)
    info_fields = Photo.info_fields()
    update_str = ', '.join(' {0} = VALUES({0})'.format(info_field) for info_field in info_fields)
    with engine.connect() as connection:
        connection.execute(Photo.__table__.insert(mysql_append_string='ON DUPLICATE KEY UPDATE ' + update_str),
                           audios_dicts)


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


