class PostMetaData:
    def __init__(self, notion_id, dev_to_id):
        self.notion_id = notion_id
        self.dev_to_id = dev_to_id

    def __str__(self):
        return "notion_id: {notion_id} dev_to_id: {dev_to_id}".format(notion_id=self.notion_id,
                                                                      dev_to_id=self.dev_to_id)
