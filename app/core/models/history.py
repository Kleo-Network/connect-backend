# from mongoengine import Document, StringField, DateTimeField
# from datetime import datetime

# class History(Document):
# 	user_address = StringField(required=True)
# 	create_timestamp = DateTimeField(default=datetime.now(datetime.UTC))
# 	title = StringField()
# 	summary = StringField()
# 	category = StringField()
# 	subcategory = StringField()
# 	url = StringField()
# 	domain = StringField()
  
# def create_history_by_user_address(user_address, create_timestamp, title, category, subcategory, url, domain):
# 	history = History(
# 		user_address=user_address,
# 		create_timestamp=create_timestamp,
# 		title=title,
# 		category=category,
# 		subcategory=subcategory,
# 		url=url,
# 		domain=domain
# 	)
# 	History.save()
# 	return history

# def get_history_by_user_address(user_address):
#     return History.object(user_address=user_address)

from datetime import datetime

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
        old_history = find_by_slug_and_time(self.document['slug'], self.document['create_timestamp'])
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