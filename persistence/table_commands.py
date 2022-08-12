import datetime
import json

from database import connection
from firebase import db
from models import PostMetaData


def create_tables():
    try:
        with connection.cursor() as cursor:
            raw_sql = open('persistence/post_metadata.sql', 'r').read()
            cursor.execute(raw_sql)
            cursor.close()
            connection.commit()
    except Exception as error:
        print(error)
    finally:
        if connection is not None:
            connection.close()


def create_post_entry(notion_id, dev_to_id, cursor):
    sql = """INSERT INTO post_metadata (notion_id, dev_to_id) VALUES(%s, %s)"""
    cursor.execute(sql, (notion_id, dev_to_id))


def seed_db():
    try:
        blog_ref = db.collection('posts')
        firebase_posts = blog_ref.get()
        with connection.cursor() as cursor:
            for post in firebase_posts:
                create_post_entry(post.id, post.get('dev_to_id'), cursor)
            cursor.close()
            connection.commit()
    except Exception as error:
        print(error)
    finally:
        connection.close()


def update_last_run_at():
    file = open("persistence/config.json", "w")
    last_run_at = {
        'last_run_at': datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    }
    file.write(json.dumps(last_run_at))
    file.close()


def get_last_run_at():
    last_run_at = None
    try:
        file = open("persistence/config.json", "r").read()
        last_run_at = json.loads(file)['last_run_at']
    except:
        pass
    return last_run_at


def get_post_metadata():
    data = []
    try:
        with connection.cursor() as cursor:
            sql = """SELECT * FROM post_metadata"""
            cursor.execute(sql)
            rows = cursor.fetchall()
            data = list(map(lambda row: PostMetaData(notion_id=row[1], dev_to_id=row[2]), rows))
            cursor.close()
    except Exception as error:
        print(error)
    finally:
        return data


get_post_metadata()
