from datetime import datetime
from flask import jsonify
import pymongo
import os
from bson import ObjectId

# MongoDB connection URI
mongo_uri = os.environ.get("DB_URL")
db_name = os.environ.get("DB_NAME")

# Connect to MongoDB
client = pymongo.MongoClient(mongo_uri)
db = client.get_database(db_name)

card_types = ("DataCard", "VisitChartCard", "DomainVisitCard")


class PublishedCard:
    def __init__(
        self,
        slug,
        type,
        content="",
        tags=[],
        urls=[],
        metadata={},
        category="Miscellaneous",
        timestamp=int(datetime.now().timestamp()),
        minted=False,
    ):
        assert isinstance(slug, str)
        assert isinstance(timestamp, int)
        assert isinstance(type, str)
        assert isinstance(content, str)
        assert isinstance(tags, list)
        assert isinstance(urls, list)
        assert isinstance(metadata, dict)
        assert isinstance(minted, bool)
        assert isinstance(category, str)

        self.document = {
            "slug": slug,
            "timestamp": timestamp,
            "type": type,
            "content": content,
            "tags": tags,
            "urls": urls,
            "metadata": metadata,
            "minted": minted,
            "category": category,
        }

    def save(self):
        if self.document["type"] not in card_types:
            return {
                "error": f"Invalid card type. Allowed types: {', '.join(card_types)}"
            }
        db.published_cards.insert_one(self.document)


def get_published_card(slug, object_id=None):
    pipeline = [{"$match": {"slug": slug}}, {"$sort": {"timestamp": -1}}]
    if object_id:  # If object_ids are provided, add match on object_ids
        pipeline[0]["$match"]["_id"] = object_id
    cards = list(db.published_cards.aggregate(pipeline))
    result = []
    for card in cards:
        card_data = {
            "id": str(card["_id"]),
            "date": format_datetime(card["timestamp"]),
            "cardType": card["type"],
            "category": card["category"],  # You can add category logic here
            "content": card["content"],
            "metadata": card["metadata"],
            "tags": card["tags"],
            "urls": card["urls"],
            "minted": card["minted"],
        }
        result.append(card_data)
    return result


def delete_published_card(slug, id):
    if not get_published_card(slug, id)[0]["minted"]:
        result = db.published_cards.delete_one({"_id": id, "slug": slug})
        if result.deleted_count == 1:
            return jsonify({"message": f"Card deleted successfully for {slug}"}), 200
        else:
            return (
                jsonify({"message": f"Card not found or already deleted for {slug}"}),
                404,
            )
    else:
        return jsonify({"error": f"card already minted by {slug}"}), 404


def count_published_cards(slug):
    count = db.published_cards.count_documents({"slug": slug})
    return count


def format_datetime(dt):
    return datetime.utcfromtimestamp(dt).strftime("%d %b %Y")


def get_published_card_with_adjacent(slug, date, card_id=None):

    if card_id:
        object_id = ObjectId(card_id)
        card = db.published_cards.find_one({"_id": object_id, "slug": slug})
    else:
        card = db.published_cards.find_one(
            {"slug": slug, "timestamp": {"$gte": date}}, sort=[("timestamp", 1)]
        )

    if not card:
        return None

    current_timestamp = card["timestamp"]

    next_card = db.published_cards.find_one(
        {"slug": slug, "timestamp": {"$gt": current_timestamp}},
        sort=[("timestamp", 1)],
        projection={"_id": 1},
    )

    prev_card = db.published_cards.find_one(
        {"slug": slug, "timestamp": {"$lt": current_timestamp, "$gte": date}},
        sort=[("timestamp", -1)],
        projection={"_id": 1},
    )

    result = {
        "card": format_card(card),
        "prevCard": str(prev_card["_id"]) if prev_card else None,
        "nextCard": str(next_card["_id"]) if next_card else None,
    }

    return result


def format_card(card):
    return {
        "id": str(card["_id"]),
        "date": format_datetime(card["timestamp"]),
        "cardType": card["type"],
        "category": card.get("category", "Miscellaneous"),
        "content": card["content"],
        "metadata": card["metadata"],
        "tags": card["tags"],
        "urls": card["urls"],
        "minted": card["minted"],
        "slug": card["slug"],
        "timestamp": card["timestamp"],
    }
