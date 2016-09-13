import logging
import shutil

import MySQLdb as Mdb
from vk_app.utils import find_file

from models import Base, engine
from settings import DB_HOST, DB_USER_NAME, DB_USER_PASSWORD, DB_NAME

# TODO: rewrite this module, define rules of database filling up

INNER_PHOTOS_TABLE_NAME = "inner_photos"
OUTER_PHOTOS_TABLE_NAME = "outer_photos"

MYSQL_PHOTOS_TABLE_UPDATE_REQUEST = '''UPDATE {}
SET vk_id = {{vk_id}}, owner_id = {{owner_id}}, user_id = {{user_id}},
album = '{{album}}', comment = '{{text}}', post_date = {{post_date}} WHERE link LIKE '%{{link}}%';'''

INNER_PHOTOS_TABLE_UPDATE_REQUEST = MYSQL_PHOTOS_TABLE_UPDATE_REQUEST.format(INNER_PHOTOS_TABLE_NAME)

INNER_PHOTOS_TABLE_INSERT_REQUEST = '''INSERT INTO {}
(vk_id, owner_id, user_id, album, link, comment, post_date, is_posted)
VALUES ({{vk_id}}, {{owner_id}}, {{user_id}}, {{album}}, {{link}}, {{comment}}, {{post_date}}, FALSE);'''.format(
    INNER_PHOTOS_TABLE_NAME
)

OUTER_PHOTOS_TABLE_UPDATE_REQUEST = MYSQL_PHOTOS_TABLE_UPDATE_REQUEST.format(OUTER_PHOTOS_TABLE_NAME)

OUTER_PHOTOS_TABLE_INSERT_REQUEST = '''INSERT INTO {}
(vk_id, owner_id, user_id, album, link, comment, post_date, is_posted)
VALUES ({{vk_id}}, {{owner_id}}, {{user_id}}, {{album}}, {{link}}, {{comment}}, {{post_date}}, FALSE);'''.format(
    INNER_PHOTOS_TABLE_NAME
)


def create_inner_photos_table():
    con = Mdb.connect(DB_HOST, DB_USER_NAME, DB_USER_PASSWORD, DB_NAME)
    with con:
        cur = con.cursor()
        cur.execute("""DROP TABLE IF EXISTS {}""".format(INNER_PHOTOS_TABLE_NAME))
        cur.execute("""CREATE TABLE {}
                 (id INT PRIMARY KEY AUTO_INCREMENT,
                 vk_id INT,
                 owner_id INT,
                 user_id INT,
                 album TEXT,
                 link TEXT,
                 comment TEXT,
                 post_date DATETIME,
                 is_posted TINYINT(1)) DEFAULT CHARSET=utf8""".format(INNER_PHOTOS_TABLE_NAME))


def create_outer_photos_table():
    con = Mdb.connect(DB_HOST, DB_USER_NAME, DB_USER_PASSWORD, DB_NAME)
    with con:
        cur = con.cursor()
        cur.execute("""DROP TABLE IF EXISTS {}""".format(OUTER_PHOTOS_TABLE_NAME))
        cur.execute("""CREATE TABLE {}
                 (id INT PRIMARY KEY AUTO_INCREMENT,
                 vk_id INT,
                 owner_id INT,
                 user_id INT,
                 album TEXT,
                 link TEXT,
                 comment TEXT,
                 post_date DATETIME) DEFAULT CHARSET=utf8""".format(OUTER_PHOTOS_TABLE_NAME))


def read_table(table_name=INNER_PHOTOS_TABLE_NAME, limit=100):
    con = Mdb.connect(DB_HOST, DB_USER_NAME, DB_USER_PASSWORD, DB_NAME)
    with con:
        cur = con.cursor()
        req = """SELECT * FROM {} LIMIT {}""".format(table_name, limit)
        cur.execute(req)
        rows = cur.fetchall()

        for row in rows:
            logging.info(row)


def check_duplicates(table_name=INNER_PHOTOS_TABLE_NAME):
    con = Mdb.connect(DB_HOST, DB_USER_NAME, DB_USER_PASSWORD, DB_NAME)
    with con:
        cur = con.cursor()

        req = """SELECT vk_id, owner_id, COUNT(*) FROM {} GROUP BY vk_id, owner_id HAVING COUNT(*) > 1""".format(
            table_name
        )
        cur.execute(req)
        res = cur.fetchall()

        for duplicate in res:
            logging.info(duplicate)
        return res


def remove_duplicates(table_name=INNER_PHOTOS_TABLE_NAME):
    con = Mdb.connect(DB_HOST, DB_USER_NAME, DB_USER_PASSWORD, DB_NAME, use_unicode=True, charset="utf8")
    with con:
        cur = con.cursor()
        req = """DELETE FROM {0} WHERE id IN (
                 SELECT all_duplicates.id FROM (
                 SELECT id FROM {0} WHERE (vk_id, owner_id) IN (
                 SELECT vk_id, owner_id FROM {0} GROUP BY vk_id, owner_id having count(*) > 1
                 )
                 ) AS all_duplicates
                 LEFT JOIN (
                 SELECT id FROM {0} GROUP BY vk_id, owner_id having count(*) > 1
                 ) AS grouped_duplicates
                 ON all_duplicates.id = grouped_duplicates.id
                 WHERE grouped_duplicates.id IS NULL)""".format(table_name)
        cur.execute(req)


RESTRICTED_ALBUMS = ['ябынестал', 'ммм', 'momspaghetti', 'разное']


def set_posted(key, value):
    con = Mdb.connect(DB_HOST, DB_USER_NAME, DB_USER_PASSWORD, DB_NAME)
    with con:
        cur = con.cursor()
        req = """UPDATE {} SET is_posted = 1 WHERE {} = {}""".format(INNER_PHOTOS_TABLE_NAME, key, value)
        cur.execute(req)


if __name__ == '__main__':
    create_outer_photos_table()
    create_inner_photos_table()


def synchronize_photos_with_photos_table(photos: list, save_path: str, is_inner_photos_table: bool):
    con = Mdb.connect(DB_HOST, DB_USER_NAME, DB_USER_PASSWORD, DB_NAME, charset="utf8")
    if is_inner_photos_table:
        photos_table_update_request = INNER_PHOTOS_TABLE_UPDATE_REQUEST
        photos_table_insert_request = INNER_PHOTOS_TABLE_INSERT_REQUEST
    else:
        photos_table_update_request = OUTER_PHOTOS_TABLE_UPDATE_REQUEST
        photos_table_insert_request = OUTER_PHOTOS_TABLE_INSERT_REQUEST

    with con:
        cur = con.cursor()
        for photo in photos:
            image_path = photo.get_image_path(save_path)
            image_name = photo.get_image_name()
            old_image_path = find_file(image_name, save_path)
            if old_image_path:
                shutil.move(old_image_path, image_path)
                req = photos_table_update_request.format(**photo.__dict__)
            else:
                req = photos_table_insert_request.format(**photo.__dict__)

            cur.execute(req)


if __name__ == '__main__':
    Base.metadata.create_all(engine)
