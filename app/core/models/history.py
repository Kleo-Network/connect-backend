from bson import ObjectId
import pymongo
from datetime import datetime
import os

# MongoDB connection URI
mongo_uri = os.environ.get("DB_URL")
db_name = os.environ.get("DB_NAME")

# Connect to MongoDB
client = pymongo.MongoClient(mongo_uri)
db = client.get_database(db_name)


class History:
    def __init__(
        self,
        address,
        title,
        category,
        subcategory,
        url,
        domain,
        summary,
        visitTime,
        create_timestamp=int(datetime.now().timestamp()),
    ):
        assert isinstance(address, str)
        assert isinstance(create_timestamp, int)
        assert isinstance(title, str)
        assert isinstance(category, str)
        assert isinstance(subcategory, str)
        assert isinstance(url, str)
        assert isinstance(domain, str)
        assert isinstance(summary, str)
        assert isinstance(visitTime, int)

        self.document = {
            "address": address,
            "create_timestamp": create_timestamp,
            "title": title,
            "category": category,
            "subcategory": subcategory,
            "url": url,
            "domain": domain,
            "summary": summary,
            "visitTime": visitTime,
        }

    def save(self):
        if find_by_address_and_time(
            self.document["address"], self.document["visitTime"], self.document["url"]
        ):
            return
        db.history.insert_one(self.document)


def find_by_address_and_time(address, visitTime, url):
    try:
        pipeline = [
            {"$match": {"address": address, "visitTime": visitTime, "url": url}},
            {"$project": {"_id": 0}},  # Exclude the _id field
        ]
        user_of_db = db.history.aggregate(pipeline).next()
        return user_of_db
    except StopIteration as _:
        return None

    except Exception as e:
        return {}


def get_history_item(address):
    pipeline = [{"$match": {"address": address}}]
    histories = list(db.history.aggregate(pipeline))
    result = []
    for history in histories:
        if "visitTime" in history:
            history_data = {
                "id": str(history["_id"]),
                "visitTime": history["visitTime"],
                "category": history["category"],
                "title": history["title"],
                "url": history["url"],
                "domain": history["domain"],
            }
            result.append(history_data)
    return result


def delete_history(address, id):
    result = db.history.delete_one({"address": address})
    if result.deleted_count == 1:
        return True
    else:
        return False


def get_history_count(address):
    count = db.history.count_documents({"address": address})
    return count


def delete_all_history(address):
    try:
        db.history.delete_many({"address": address})
    except Exception as e:
        print(e)
        return 0


def get_top_activities(address):
    histories = get_history_item(address)
    activities = [history["category"] for history in histories]
    activity_counts = Counter(activities)
    total_activities = sum(activity_counts.values())
    activity_percentages = [
        {"label": activity, "percentage": round((count / total_activities) * 100)}
        for activity, count in activity_counts.items()
    ]
    top_activities = sorted(
        activity_percentages, key=lambda x: x["percentage"], reverse=True
    )[:8]
    return top_activities
