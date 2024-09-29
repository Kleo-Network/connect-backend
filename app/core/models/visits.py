from bson import ObjectId
import pymongo
from datetime import datetime, timedelta
import os

# MongoDB connection URI
mongo_uri = os.environ.get("DB_URL")
db_name = os.environ.get("DB_NAME")

# Connect to MongoDB
client = pymongo.MongoClient(mongo_uri)
db = client.get_database(db_name)


class Visits:
    def __init__(
        self,
        slug,
        category,
        domain,
        visitTime,
        create_timestamp=int(datetime.now().timestamp()),
    ):
        assert isinstance(slug, str)
        assert isinstance(create_timestamp, int)
        assert isinstance(category, str)
        assert isinstance(domain, str)
        assert isinstance(visitTime, int)

        self.document = {
            "slug": slug,
            "create_timestamp": create_timestamp,
            "category": category,
            "domain": domain,
            "visitTime": visitTime,
        }

    def save(self):
        if find_by_slug_and_time(
            self.document["slug"], self.document["visitTime"], self.document["domain"]
        ):
            return
        db.visits.insert_one(self.document)


def find_by_slug_and_time(slug, visitTime, domain):
    try:
        pipeline = [
            {"$match": {"slug": slug, "visitTime": visitTime, "domain": domain}},
            {"$project": {"_id": 0}},  # Exclude the _id field
        ]
        user_of_db = db.visits.aggregate(pipeline).next()
        return user_of_db
    except StopIteration as _:
        return None

    except Exception as e:
        return {}


def fetch_visits_for_week(slug, start_date, end_date):
    pipeline = [
        {
            "$match": {
                "visitTime": {
                    "$gte": int(start_date.timestamp()),
                    "$lte": int(end_date.timestamp()),
                },
                "slug": slug,
            }
        },
        {"$group": {"_id": "$domain", "count": {"$sum": 1}}},
    ]
    return {doc["_id"]: doc["count"] for doc in db.visits.aggregate(pipeline)}


def fetch_visits_for_last_15_days(slug):
    today = datetime.today()
    start_date = (today - timedelta(days=15)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)

    pipeline = [
        {
            "$match": {
                "visitTime": {
                    "$gte": int(start_date.timestamp()),
                    "$lte": int(end_date.timestamp()),
                },
                "slug": slug,
            }
        },
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 8},
    ]
    return list(db.visits.aggregate(pipeline))
