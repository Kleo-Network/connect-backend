from datetime import datetime
from flask import jsonify

import pymongo
from datetime import datetime
import os

# MongoDB connection URI
mongo_uri = os.environ.get("DB_URL")
db_name = os.environ.get("DB_NAME")

# Connect to MongoDB
client = pymongo.MongoClient(mongo_uri)
db = client.get_database(db_name)

card_types= ("DataCard", "ImageCard", "DomainVisitCard", "IconCard")

class PendingCard():
    def __init__(self, slug, type, content="",
                 tags=[], urls={}, metadata={}, category="Miscellaneous", timestamp=int(datetime.now().timestamp())):
        assert isinstance(slug, str)
        assert isinstance(timestamp, int)
        assert isinstance(type, str)
        assert isinstance(content, str)
        assert isinstance(tags, list)
        assert isinstance(urls, dict)
        assert isinstance(metadata, dict)
        assert isinstance(category, str)
        
        self.document = {
            'slug': slug,
            'timestamp': timestamp,
            'type': type,
            'content': content,
            'tags': tags,
            'urls': urls,
            'metadata': metadata,
            'category': category
        }
        
    def save(self):
        if self.document['type'] not in card_types:
            return {"error": f"Invalid card type. Allowed types: {', '.join(card_types)}"}
        db.pending_cards.insert_one(self.document)

def get_pending_card(slug, object_id=None):
    pipeline = [
        {"$match": {"slug": slug}},
        {"$sort": {"timestamp": -1}}
    ]
    if object_id:  # If object_ids are provided, add match on object_ids
        pipeline[0]["$match"]["_id"] = object_id
    cards = list(db.pending_cards.aggregate(pipeline))
    result = []
    for card in cards:
        card_data = {
            "id": str(card['_id']),
            "date": card['timestamp'],
            "cardType": card['type'],
            "category": card['category'],  
            "tags": card['tags'],
            "urls": card['urls'],
            "content": card['content'],
            "metadata": card['metadata']
        }
        result.append(card_data)
    return result

def delete_pending_card(slug, id):
    result = db.pending_cards.delete_one({'_id': id, 'slug': slug})
    if result.deleted_count == 1:
        return jsonify({'message': f'Card deleted successfully for {slug}'}), 200
    else:
        return jsonify({'message': f'Card not found or already deleted for {slug}'}), 404

