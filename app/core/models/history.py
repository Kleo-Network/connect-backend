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
    def __init__(self, slug, title, category, subcategory, url, domain, summary, create_timestamp = int(datetime.now().timestamp())):
        assert isinstance(slug, str)
        assert isinstance(create_timestamp, int)
        assert isinstance(title, str)
        assert isinstance(category, str)
        assert isinstance(subcategory, str)
        assert isinstance(url, str)
        assert isinstance(domain, str)
        assert isinstance(summary, str)
        
        self.document = {
            'slug': slug,
            'create_timestamp': create_timestamp,
            'title': title,
            'category': category,
            'subcategory': subcategory,
            'url': url,
            'domain': domain,
            'summary': summary
        }
        
    def save(self):
        print(self.document)
        db.history.insert_one(self.document)
        
def find_by_slug_and_time(slug, create_timestamp):
    try:
        pipeline = [
            {
                "$match": {
                    "slug": slug,
                    "create_timestamp": create_timestamp
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
    hstories = list(db.history.aggregate(pipeline))
    result = []
    for history in hstories:
        history_data = {
            "id": str(history['_id']),
            "title": history['title'],
            "category": history['category'],  # You can add category logic here
            "subcategory": history['subcategory'],
            "domain": history['domain'],
            "summary": history['summary'],
            "url": history['url'],
            "minted": history['minted']
        }
        result.append(history_data)
    return result