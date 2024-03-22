from datetime import datetime
from flask import jsonify
import pymongo
import os
from bson.objectid import ObjectId

# MongoDB connection URI
mongo_uri = os.environ.get("DB_URL")
db_name = os.environ.get("DB_NAME")

# Connect to MongoDB
client = pymongo.MongoClient(mongo_uri)
db = client.get_database(db_name)

card_types= ("TextCard", "CalendarCard", "PlaceCard", "InstaCard", "XCard", "GitCard", "LinkedinCard")

class StaticCards():
    def __init__(self, slug, type, last_connected, metadata={}):
        assert isinstance(slug, str)
        assert isinstance(type, str)
        assert isinstance(metadata, dict)
        assert isinstance(last_connected, int)
        
        self.document = {
            'slug': slug,
            'last_connected': last_connected,
            'type': type,
            'metadata': metadata
        }
        
    def save(self):
        if self.document['type'] not in card_types:
            return {"error": f"Invalid card type. Allowed types: {', '.join(card_types)}"}
        existing_card = find_static_cards_by_slug(self.document['slug'], self.document['type'])
        if existing_card:
            update_static_card(self.document['slug'], self.document['type'], self.document['metadata'], existing_card['_id'])
        else:
            db.static_cards.insert_one(self.document)

def get_static_card(slug):
    pipeline = [
        {"$match": {"slug": slug}}
    ]
    cards = list(db.static_cards.aggregate(pipeline))
    result = []
    for card in cards:
        card_data = {
            "id": str(card['_id']),
            "last_connected": format_datetime(card['last_connected']),
            "cardType": card['type'],
            "metadata": card['metadata']
        }
        result.append(card_data)
    return result

def update_static_card(slug, type, metadata, card_id = None):
    try:
        filter_query = {"slug": slug, "type": type}
        if card_id:
            filter_query["_id"]= ObjectId(card_id)
        print(filter_query)
        update_operation = {
            "$set": {
                "metadata": metadata
            }
        }
        user_of_db = db.static_cards.find_one_and_update(filter_query, update_operation, projection={"_id": {"$toString": "$_id"}}, return_document = pymongo.ReturnDocument.AFTER)
        return user_of_db

    # TODO: Error Handling
    # If an invalid ID is passed to `get_movie`, it should return None.
    except (StopIteration) as _:
        return None

    except Exception as e:
        print(e)
        return {}

def delete_static_card(slug, ids):
    result = db.static_cards.delete_many({'_id': {'$in': ids}, 'slug': slug})
    if result.deleted_count > 0:
        return jsonify({'message': f'{result.deleted_count} static card(s) belonging to user {slug} deleted successfully'}), 200
    else:
        return jsonify({'error': f'No cards found with the provided IDs for user {slug}'}), 404
    
def find_static_cards_by_slug(slug, type):
    try:
        pipeline = [
            {
                "$match": {
                    "slug": slug,
                    "type": type
                }
            },
            {
                "$project": {
                "_id": {"$toString": "$_id"}
                }
            }
        ]
        card = db.static_cards.aggregate(pipeline).next()
        return card

    # TODO: Error Handling
    # If an invalid ID is passed to `get_movie`, it should return None.
    except (StopIteration) as _:
        return None

    except Exception as e:
        return {}

def format_datetime(dt):
    return datetime.utcfromtimestamp(dt).strftime("%d %b %Y")
