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
                 identity_tags=[], badges=[], profile_metadata={}, settings={},first_time_user=True):
        
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
        assert isinstance(first_time_user, bool)
        
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
            'settings': settings,
            'first_time_user': first_time_user
        }

    def save(self, signup):
        existing_user_address = find_by_address(self.document['address'])
        if existing_user_address:
            return existing_user_address
        existing_user_slug = find_by_slug(self.document['slug'])
        if existing_user_slug:
            return existing_user_slug
        if signup:
            self.document['stage'] = self.document.get('stage') or 1
            self.document['last_cards_marked'] = self.document.get('last_cards_marked') or int(datetime.now().timestamp())
            self.document['last_attested'] = self.document.get('last_attested') or int(datetime.now().timestamp())
            user_collection.insert_one(self.document)
            return find_by_slug(self.document['slug'])
        return {}

def set_signup_upload_by_slug(slug):
    try:
        filter_query = {"slug": slug}
        update_operation = {
            "$set": {
                "first_time_user": False
            }
        }
        user_of_db = db.users.find_one_and_update(filter_query, update_operation, projection={"_id": 0}, return_document=pymongo.ReturnDocument.AFTER)
        return user_of_db

    except (StopIteration) as _:
        return None

    except Exception as e:
        print(e)
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
                    "_id": 0,  # Exclude the _id field
                    "address": 0
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
    
def find_by_address_slug(slug):
    try:
        pipeline = [
            {
                "$match": {
                    "slug": slug
                }
            }
        ]
        user_of_db = db.users.aggregate(pipeline).next()
        return user_of_db['address']

    # TODO: Error Handling
    # If an invalid ID is passed to `get_movie`, it should return None.
    except (StopIteration) as _:
        return None

    except Exception as e:
        return {}
    
def find_by_address(address):
    try:
        pipeline = [
            {
                "$match": {
                    "address": address
                }
            },
            {
                "$project": {
                    "_id": 0,  # Exclude the _id field
                    "address": 0
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
    slug_from_db = db.users.find({}, {'slug': 1})
    user_slugs = [user['slug'] for user in slug_from_db if 'slug' in user]
    return user_slugs

def update_last_cards_marked(slug):
    try:
        db.users.update_one({'slug': slug}, {'$set': {'last_cards_marked': int(datetime.now().timestamp())}})

    # TODO: Error Handling
    # If an invalid ID is passed to `get_movie`, it should return None.
    except (StopIteration) as _:
        return None

    except Exception as e:
        print(e)
        return {}
    
def update_last_attested(slug):
    try:
        db.users.update_one({'slug': slug}, {'$set': {'last_attested': int(datetime.now().timestamp())}})
    except Exception as e:
        print(e)
        return {}
    
def update_minting_count(slug):
    try:
        pipeline = [
            {
                "$match": {
                    "slug": slug
                }
            }
        ]
        
        # Execute the pipeline and get the user
        cursor = db.users.aggregate(pipeline)
        user = next(cursor, None)
        
        if user:
            user_profile_metadata = user.get('profile_metadata', {})
            mint_count = user_profile_metadata.get('mint_count', 0)
            
            if user_profile_metadata and mint_count:
                mint_count_updated = int(mint_count) + 1
                user_profile_metadata['mint_count'] = mint_count_updated
            else:
                user_profile_metadata['mint_count'] = 1
            db.users.update_one({'slug': slug}, {'$set': {'profile_metadata': user_profile_metadata}})
    except Exception as e:
        print(e)
        return {}