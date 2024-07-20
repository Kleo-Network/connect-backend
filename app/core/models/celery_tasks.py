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
        assert isinstance(task_id, str)
        assert isinstance(type_, str)
        assert isinstance(status, str)
        assert isinstance(timestamp, int)
        
        self.document = {
            'slug': slug,
            'task_id': task_id,
            'type_': type_,
            'status': status,
            'timestamp': timestamp
        }
        
    def save(self):
        if find_by_slug_and_task_id(self.document['slug'], self.document['task_id']):
            return
        db.celery.insert_one(self.document)

def get_celery_tasks_by_slug(slug):
    """
    Retrieve all celery tasks for a given user slug.
    
    :param slug: The user's slug
    :return: List of celery tasks
    """
    pipeline = [
        {"$match": {"slug": slug}},
        {"$project": {
            "_id": {"$toString": "$_id"},
            "task_id": 1,
            "type_": 1,
            "status": 1,
            "slug": 1,
            "timestamp": 1
        }}
    ]
    print(pipeline)
    tasks = list(db.celery.aggregate(pipeline))
    print(tasks)
    return tasks

def get_all_celery_tasks():
    """
    Retrieve all celery tasks for all users.
    
    :return: List of all celery tasks
    """
    pipeline = [
        {"$project": {
            "_id": {"$toString": "$_id"},
            "slug": 1,
            "task_id": 1,
            "type_": 1,
            "status": 1,
            "timestamp": 1
        }}
    ]
    
    tasks = list(db.celery.aggregate(pipeline))
    return tasks

def find_by_slug_and_task_id(slug, task_id):
    """
    Find a specific celery task by slug and task_id.
    
    :param slug: The user's slug
    :param task_id: The task ID
    :return: The task document or None if not found
    """
    task = db.celery.find_one({"slug": slug, "task_id": task_id})
    if task:
        task['_id'] = str(task['_id'])
    return task

def update_celery_task_status(slug, task_id, new_status):
    """
    Update the status of a celery task. If the new status is "SUCCESS", delete the task.
    
    :param slug: The user's slug
    :param task_id: The task ID
    :param new_status: The new status to set
    :return: The updated task document, None if deleted, or None if not found
    """
    if new_status == "SUCCESS":
        # Delete the task if the status is SUCCESS
        result = db.celery.delete_one({"slug": slug, "task_id": task_id})
        return None if result.deleted_count > 0 else None
    else:
        # Update the task status
        updated_task = db.celery.find_one_and_update(
            {"slug": slug, "task_id": task_id},
            {"$set": {"status": new_status, "timestamp": int(datetime.now().timestamp())}},
            return_document=pymongo.ReturnDocument.AFTER
        )
        if updated_task:
            updated_task['_id'] = str(updated_task['_id'])
        return updated_task