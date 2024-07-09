from bson import ObjectId
import pymongo
from datetime import datetime
import os

# MongoDB connection URI
mongo_uri = os.environ.get("DB_URL")
db_name = os.environ.get("DB_NAME")

# Connect to MongoDB
client = pymongo.MongoClient(mongo_uri)
db = client.get_database(db_name)

class CeleryTask():
    def __init__(self, slug, task_id, type_, status, timestamp = int(datetime.now().timestamp())):
        assert isinstance(slug, str)
        assert isinstance(task_id, int)
        assert isinstance(type_, str)
        assert isinstance(status, str)
        assert isinstance(timestamp, int)
        
        self.document = {
            'slug': slug,
            'task_id': task_id,
            'type_': type_,
            'status': status,
            'timestamp': visitTime
        }
        
    def save(self):
        if find_by_slug_and_task_id(self.document['slug'], self.document['task_id']):
            return
        db.celery.insert_one(self.document)