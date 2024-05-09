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

class History():
    def __init__(self, slug, title, category, subcategory, url, domain, summary, visitTime, create_timestamp = int(datetime.now().timestamp())):
        assert isinstance(slug, str)
        assert isinstance(create_timestamp, int)
        assert isinstance(title, str)
        assert isinstance(category, str)
        assert isinstance(subcategory, str)
        assert isinstance(url, str)
        assert isinstance(domain, str)
        assert isinstance(summary, str)
        assert isinstance(visitTime, int)
        
        self.document = {
            'slug': slug,
            'create_timestamp': create_timestamp,
            'title': title,
            'category': category,
            'subcategory': subcategory,
            'url': url,
            'domain': domain,
            'summary': summary,
            'visitTime': visitTime
        }
        
    def save(self):
        if find_by_slug_and_time(self.document['slug'], self.document['visitTime'], self.document['url']):
            return
        db.history.insert_one(self.document)
        
def find_by_slug_and_time(slug, visitTime, url):
    try:
        pipeline = [
            {
                "$match": {
                    "slug": slug,
                    "visitTime": visitTime,
                    "url": url
                }
            },
            {
                "$project": {
                    "_id": 0  # Exclude the _id field
                }
            }
        ]
        user_of_db = db.history.aggregate(pipeline).next()
        return user_of_db
    except (StopIteration) as _:
        return None

    except Exception as e:
        return {}
        
def get_history_item(slug):
    pipeline = [
        {"$match": {"slug": slug}}
    ]
    histories = list(db.history.aggregate(pipeline))
    result = []
    for history in histories:
        history_data = {
            "id": str(history['_id']),
            "visitTime": history['visitTime'],
            "category": history['category'],
            "title": history['title'],
            "url": history['url'],
            "domain": history['domain']
        }
        result.append(history_data)
    return result

def delete_history(slug, id):
    result = db.history.delete_one({'slug': slug})
    if result.deleted_count == 1:
        return True
    else:
        return False

def get_history_count(slug):
    count = db.history.count_documents({'slug': slug})
    return count