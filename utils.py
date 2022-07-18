class Operations:
    CREATE = 'create'
    EDIT = 'edit'


class PostOperation:
    def __init__(self, operation: str, page_id, dev_to_id = None):
        self.operation = operation
        self.id = page_id
        self.dev_to_id = dev_to_id


class NotionBlogOutput:
    def __init__(self, title, body):
        self.title = title
        self.body = body