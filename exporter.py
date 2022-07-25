import asyncio
import io
import json
from zipfile import ZipFile

import requests

from utils import NotionBlogOutput

notion_token: str = '82b22234beceb21591541f56069ae21fd63f43324cba097651d5c1264461fa07d9d2845e4422300014d1899b7076af297eef91a2c88af58e2f1b666c8c83cde4bfa9c18e2bff38be80ff178b1bbd'
notion_export_headers = {'Cookie': f'token_v2={notion_token}', 'Content-Type': 'application/json'}
dev_to_article_url = 'https://dev.to/api/articles'


def create_export_task(block_id: str):
    print('Enqueuing task')
    response = requests.post('https://www.notion.so/api/v3/enqueueTask',
                             headers=notion_export_headers,
                             data=json.dumps({'task': {
                                 'eventName': 'exportBlock',
                                 'request': {
                                     'block': {
                                         'id': block_id
                                     },
                                     'recursive': False,
                                     'exportOptions': {
                                         'exportType': 'markdown',
                                         'timeZone': 'Europe/Zurich',
                                         'locale': 'en'
                                     }
                                 }
                             }}
                             )
                             )
    task_id = response.json()['taskId']
    print(f'task_id {task_id}')
    return task_id


async def get_export_url_from_task(task_id: str):
    response = requests.post('https://www.notion.so/api/v3/getTasks',
                             headers=notion_export_headers,
                             timeout=10,
                             data=json.dumps({'taskIds': [task_id]}))
    results = response.json()['results']
    task = next(task for task in results if task['id'] == task_id)
    if task['state'] == 'success':
        return task['status']['exportURL']
    elif task['state'] == 'in_progress':
        print('task still in progress')
        await asyncio.sleep(10)
        new_task = asyncio.create_task(get_export_url_from_task(task_id))
        return await new_task
    else:
        raise Exception('Export task failed')


def get_blog_data_from_url(export_url: str) -> NotionBlogOutput:
    print('Getting exported file')
    response = requests.get(export_url, stream=True)
    data = None
    for chunk in response.iter_content():
        if data is None:
            data = chunk
        else:
            data += chunk
    zip = ZipFile(io.BytesIO(data), 'r')
    page = zip.namelist()[0]
    with zip.open(name=page, mode='r') as input:
        title = input.readline().decode().replace('# ', '').strip()
        content = input.read().decode('utf-8')
        return NotionBlogOutput(title=title, body=content)


def create_post_on_dev_to(post: NotionBlogOutput):
    headers = {
        'api-key': 'r2Ry6BmhS9LbRRa6nq5uyPNn',
        'Content-Type': 'application/json'
    }
    body = json.dumps({
        'article': {
            'title': post.title,
            'published': True,
            'body_markdown': post.body
        }
    })
    response = requests.post(dev_to_article_url, headers=headers, data=body)
    return response.json()


def edit_post_on_dev_to(post: NotionBlogOutput, dev_to_post_id):
    headers = {
        'api-key': 'r2Ry6BmhS9LbRRa6nq5uyPNn',
        'Content-Type': 'application/json'
    }
    body = json.dumps({
        'article': {
            'title': post.title,
            'published': True,
            'body_markdown': post.body
        }
    })
    response = requests.put(f'{dev_to_article_url}/{dev_to_post_id}', headers=headers, data=body)
    return response.json()
