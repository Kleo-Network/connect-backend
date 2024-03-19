from datetime import datetime
from flask import jsonify
import pymongo
import os

# MongoDB connection URI
mongo_uri = os.environ.get("DB_URL")
db_name = os.environ.get("DB_NAME")

# Connect to MongoDB
client = pymongo.MongoClient(mongo_uri)
db = client.get_database(db_name)

card_types= ("DataCard", "ImageCard", "DomainVisitCard", "IconCard")

class PublishedCard():
    def __init__(self, user_address, timestamp, type, content="",
                 tags=[], urls=[], metadata={}):
        assert isinstance(user_address, str)
        assert isinstance(timestamp, int)
        assert isinstance(type, str)
        assert isinstance(content, str)
        assert isinstance(tags, list)
        assert isinstance(urls, list)
        assert isinstance(metadata, dict)
        
        self.document = {
            'user_address': user_address,
            'timestamp': timestamp,
            'type': type,
            'content': content,
            'tags': tags,
            'urls': urls,
            'metadata': metadata
        }
        
        def save(self):
            self.document['timestamp'] = self.document.get('timestamp') or int(datetime.now().timestamp())
            if self.type not in card_types:
                return {"error": f"Invalid card type. Allowed types: {', '.join(card_types)}"}
            db.published_cards.insert_one(self.document)

def get_published_card(user_address):
    pipeline = [
        {"$match": {"user_address": user_address}}
    ]
    cards = list(db.published_cards.aggregate(pipeline))
    result = []
    for card in cards:
        card_data = {
            "id": str(card['_id']),
            "date": format_datetime(card['timestamp']),
            "cardType": card['type'],
            "category": "",  # You can add category logic here
            "content": card['content'],
            "metadata": card['metadata']
        }
        result.append(card_data)
    return result

def delete_published_card(user_address, ids):
    result = db.published_cards.delete_many({'_id': {'$in': ids}, 'user_address': user_address})
    if result.deleted_count > 0:
        return jsonify({'message': f'{result.deleted_count} card(s) belonging to user at address {user_address} deleted successfully'}), 200
    else:
        return jsonify({'error': f'No cards found with the provided IDs for user at address {user_address}'}), 404

def format_datetime(dt):
    return datetime.utcfromtimestamp(dt).strftime("%d %b %Y")
