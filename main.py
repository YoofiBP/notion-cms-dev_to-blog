import asyncio
import json
import os

import requests
import rollbar
from dotenv import load_dotenv
from google.cloud.firestore_v1.field_path import FieldPath

from exporter import create_export_task, get_export_url_from_task, get_blog_data_from_url, create_post_on_dev_to, \
    edit_post_on_dev_to
from firebase import db
from utils import Operations, PostOperation, update_last_run_at

load_dotenv()

rollbar.init('603d18c0aa044c678521f6c7430fc3e2')

notion_api_secret: str = os.environ['NOTION_API_SECRET']
notion_blog_database_id: str = os.environ['NOTION_BLOG_DATABASE_ID']
notion_api_version: str = os.environ['NOTION_API_VERSION']

notion_api_blog_pages_endpoint = f'https://api.notion.com/v1/databases/{notion_blog_database_id}/query'
notion_required_headers = {'Authorization': f'Bearer {notion_api_secret}', 'Notion-Version': notion_api_version}


def get_last_run_at() -> str:
    last_run_at = None
    try:
        config_ref = db.collection('config')
        last_run_at = config_ref.document(u'config').get().to_dict()['last_run_at']
    except:
        pass
    return last_run_at


async def main():
    try:
        print('Getting Blog Pages from Notion')
        last_run_date = get_last_run_at()
        blog_pages_filter = {}
        if last_run_date is not None:
            blog_pages_filter = json.dumps({
                "filter": {
                    "timestamp": "last_edited_time",
                    "last_edited_time": {
                        "after": last_run_date
                    }
                }
            })
        response = requests.post(notion_api_blog_pages_endpoint,
                                 headers={**notion_required_headers, 'Content-Type': 'application/json'},
                                 data=blog_pages_filter)
        blog_pages_from_notion = response.json()['results']
        notion_pages_ids = []
        for notion_page in blog_pages_from_notion:
            notion_pages_ids.append(notion_page['id'])
        if len(notion_pages_ids) == 0:
            return

        print('Getting Blog Pages from Firebase')
        blog_ref = db.collection(u'posts')

        firebase_posts = blog_ref.where(FieldPath.document_id(), u'in', notion_pages_ids).get()
        firebase_posts_dict = {}

        for firebase_post in firebase_posts:
            firebase_posts_dict[firebase_post.id] = firebase_post

        blogs_to_post = []

        for page in blog_pages_from_notion:
            if page['id'] not in firebase_posts_dict.keys():
                blogs_to_post.append(PostOperation(operation=Operations.CREATE, page_id=page['id']))
            else:
                blogs_to_post.append(PostOperation(operation=Operations.EDIT,
                                                   page_id=page['id'],
                                                   dev_to_id=firebase_posts_dict[page['id']].get('dev_to_id')))

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
                    u'dev_to_id': response['id']
                })
            elif blog.operation == Operations.EDIT:
                response = edit_post_on_dev_to(blog_data, blog.dev_to_id)
                db.collection(u'posts').document(blog.id).set({
                    u'dev_to_id': response['id']
                })
                pass
            else:
                raise Exception('Unrecognised operation')
            number_of_pages -= 1
        update_last_run_at()
    except Exception as err:
        if os.environ['ENVIRONMENT'] == 'production':
            rollbar.report_exc_info()
        else:
            raise err


asyncio.run(main())
