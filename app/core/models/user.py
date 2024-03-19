import pymongo
from datetime import datetime
import os

# MongoDB connection URI
mongo_uri = os.environ.get("DB_URL")
db_name = os.environ.get("DB_NAME")

# Connect to MongoDB
client = pymongo.MongoClient(mongo_uri)
db = client.get_database(db_name)

# Define the User collection
user_collection = db['users']

class User:
    def __init__(self, address, slug, stage, name="", pfp="", verified=False, last_cards_marked=0,
                 about="", content_tags=[], last_attested=0,
                 identity_tags=[], badges=[], profile_metadata={}, settings={}):
        
        assert isinstance(address, str)
        assert isinstance(slug, str)
        assert isinstance(name, str)
        assert isinstance(stage, int)
        assert isinstance(verified, bool)
        assert isinstance(last_cards_marked, int)
        assert isinstance(about, str)
        assert isinstance(pfp, str)
        assert isinstance(content_tags, list)
        assert isinstance(last_attested, int)
        assert isinstance(identity_tags, list)
        assert isinstance(badges, list)
        assert isinstance(profile_metadata, dict)
        assert isinstance(settings, dict)
        
        self.document = {
            'address': address,
            'slug': slug,
            'name': name,
            'stage': stage,
            'verified': verified,
            'last_cards_marked': last_cards_marked,
            'about': about,
            'pfp': pfp,
            'content_tags': content_tags,
            'last_attested': last_attested,
            'identity_tags': identity_tags,
            'badges': badges,
            'profile_metadata': profile_metadata,
            'settings': settings # to store data of the static cards
        }

    def save(self, signup):
        existing_user = find_by_slug(self.document['slug'])
        if existing_user:
            return existing_user
        if signup:
            self.document['stage'] = self.document.get('stage') or 1
            self.document['last_cards_marked'] = self.document.get('last_cards_marked') or int(datetime.now().timestamp())
            self.document['last_attested'] = self.document.get('last_attested') or int(datetime.now().timestamp())
            user_collection.insert_one(self.document)
            return find_by_slug(self.document['slug'])
        return {}
        
def find_by_slug(slug):
    try:
        pipeline = [
            {
                "$match": {
                    "slug": slug
                }
            },
            {
                "$project": {
                    "_id": 0  # Exclude the _id field
                }
            }
        ]
        user_of_db = db.users.aggregate(pipeline).next()
        return user_of_db

    # TODO: Error Handling
    # If an invalid ID is passed to `get_movie`, it should return None.
    except (StopIteration) as _:
        return None

    except Exception as e:
        return {}
    
def update_by_slug(address, slug, stage, name="", verified=False, about="", pfp="", content_tags=[],
                      identity_tags=[], badges=[], profile_metadata={}):
    try:
        filter_query = {"slug": slug}
        update_operation = {
            "$set": {
                "address": address,
                "name": name,
                "slug": slug,
                "stage": stage,
                "verified": verified,
                "about": about,
                "pfp": pfp,
                "content_tags": content_tags,
                "identity_tags": identity_tags,
                "badges": badges,
                "profile_metadata": profile_metadata
            }
        }
        user_of_db = db.users.find_one_and_update(filter_query, update_operation, projection={"_id": 0}, return_document = pymongo.ReturnDocument.AFTER)
        return user_of_db

    # TODO: Error Handling
    # If an invalid ID is passed to `get_movie`, it should return None.
    except (StopIteration) as _:
        return None

    except Exception as e:
        print(e)
        return {}
    
def update_settings_by_slug(slug, settings, stage, about):
    try:
        filter_query = {"slug": slug}
        update_operation = {
            "$set": {
                "settings": settings,
                "stage": stage,
                "about": about
            }
        }
        user_of_db = db.users.find_one_and_update(filter_query, update_operation, projection={"_id": 0}, return_document = pymongo.ReturnDocument.AFTER)
        return user_of_db

    # TODO: Error Handling
    # If an invalid ID is passed to `get_movie`, it should return None.
    except (StopIteration) as _:
        return None

    except Exception as e:
        print(e)
        return {}
    
def fetch_user_slug():
    user = db.users.find({}, {'slug': 1})
    user_slugs = [user['slug'] for user in user if 'slug' in user]
    return user_slugs