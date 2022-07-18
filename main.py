import asyncio
import datetime

from dotenv import load_dotenv
import os
import requests
from firebase import db
from dateutil.parser import parse
from exporter import create_export_task, get_export_url_from_task, get_blog_data_from_url, create_post_on_dev_to, edit_post_on_dev_to
from utils import Operations, PostOperation

load_dotenv()

notion_api_secret: str = os.environ['NOTION_API_SECRET']
notion_blog_database_id: str = os.environ['NOTION_BLOG_DATABASE_ID']
notion_api_version: str = os.environ['NOTION_API_VERSION']

notion_api_blog_pages_endpoint = f'https://api.notion.com/v1/databases/{notion_blog_database_id}/query'
notion_required_headers = {'Authorization': f'Bearer {notion_api_secret}', 'Notion-Version': notion_api_version}


async def main():
    print('Getting Blog Pages from Notion')
    response = requests.post(notion_api_blog_pages_endpoint,
                             headers=notion_required_headers)
    blog_pages_from_notion = response.json()['results']
    print('Getting Blog Pages from Firebase')
    blog_ref = db.collection(u'posts')
    firebase_posts = blog_ref.get()
    firebase_posts_dict = {}

    for firebase_post in firebase_posts:
        firebase_posts_dict[firebase_post.id] = firebase_post

    blogs_to_post = []

    for page in blog_pages_from_notion:
        if page['id'] not in firebase_posts_dict.keys():
            blogs_to_post.append(PostOperation(operation=Operations.CREATE, page_id=page['id']))
        elif parse(page['last_edited_time']) > parse(firebase_posts_dict[page['id']].get('last_updated')):
            blogs_to_post.append(PostOperation(operation=Operations.EDIT,
                                               page_id=page['id'],
                                               dev_to_id=firebase_posts_dict[page['id']].get('dev_to_id')))
        else:
            print('Skipped')

    number_of_pages = len(blogs_to_post)

    for blog in blogs_to_post:
        print(f'{number_of_pages} remaining')
        page_id = blog.id
        task_id = create_export_task(page_id)
        export_url = await get_export_url_from_task(task_id)
        blog_data = get_blog_data_from_url(export_url)
        if blog.operation == Operations.CREATE:
            print('Creating post')
            response = create_post_on_dev_to(blog_data)
            print('Updating firebase')
            db.collection(u'posts').document(blog.id).set({
                u'dev_to_id': response['id'],
                u'last_updated': datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
            })
        elif blog.operation == Operations.EDIT:
            response = edit_post_on_dev_to(blog_data, blog.dev_to_id)
            db.collection(u'posts').document(blog.id).set({
                u'dev_to_id': response['id'],
                u'last_updated': datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
            })
            pass
        else:
            raise Exception('Unrecognised operation')
        number_of_pages -= 1


asyncio.run(main())
