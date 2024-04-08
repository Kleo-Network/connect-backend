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
    def __init__(self, slug, type, content="",
                 tags=[], urls={}, metadata={},  timestamp = int(datetime.now().timestamp()), minted=False):
        assert isinstance(slug, str)
        assert isinstance(timestamp, int)
        assert isinstance(type, str)
        assert isinstance(content, str)
        assert isinstance(tags, list)
        assert isinstance(urls, dict)
        assert isinstance(metadata, dict)
        assert isinstance(minted, bool)
        
        self.document = {
            'slug': slug,
            'timestamp': timestamp,
            'type': type,
            'content': content,
            'tags': tags,
            'urls': urls,
            'metadata': metadata,
            'minted': minted
        }
        
    def save(self):
        if self.document['type'] not in card_types:
            return {"error": f"Invalid card type. Allowed types: {', '.join(card_types)}"}
        db.published_cards.insert_one(self.document)

def get_published_card(slug, object_id=None):
    pipeline = [
        {"$match": {"slug": slug}},
        {"$sort": {"timestamp": -1}}
    ]
    if object_id:  # If object_ids are provided, add match on object_ids
        pipeline[0]["$match"]["_id"] = object_id
    cards = list(db.published_cards.aggregate(pipeline))
    result = []
    for card in cards:
        card_data = {
            "id": str(card['_id']),
            "date": format_datetime(card['timestamp']),
            "cardType": card['type'],
            "category": "",  # You can add category logic here
            "content": card['content'],
            "metadata": card['metadata'],
            "tags": card['tags'],
            "urls": card['urls'],
            "minted": card['minted']
        }
        result.append(card_data)
    return result

def delete_published_card(slug, id):
    if not get_published_card(slug, id)[0]['minted']:
        result = db.published_cards.delete_one({'_id': id, 'slug': slug})
        if result.deleted_count == 1:
            return jsonify({'message': f'Card deleted successfully for {slug}'}), 200
        else:
            return jsonify({'message': f'Card not found or already deleted for {slug}'}), 404
    else:
        return jsonify({'error': f'card already minted by {slug}'}), 404
    
def mint_cards(slug):
    cards = db.published_cards.find({'slug': slug, 'minted': False})

    if cards:
        for card in cards:
            # Update the minted field to true
            db.published_cards.update_one({'_id': card['_id']}, {'$set': {'minted': True}})
        return (f"Minted field updated to true for all cards of user '{slug}'")
    else:
        return (f"No unpublished cards found for user '{slug}'")

def format_datetime(dt):
    return datetime.utcfromtimestamp(dt).strftime("%d %b %Y")
