import pymongo
from datetime import datetime, timezone
import os
import ssl


# MongoDB connection URI

mongo_uri = os.environ.get("DB_URL")
db_name = os.environ.get("DB_NAME")

# Connect to MongoDB
client = pymongo.MongoClient(mongo_uri)
db = client.get_database(db_name)

# Define the User collection
user_collection = db["users"]


class User:
    def __init__(
        self,
        address,
        slug,
        stage=1,
        name="",
        pfp="",
        previous_hash="",
        verified=False,
        last_cards_marked=0,
        about="",
        content_tags=[],
        last_attested=0,
        identity_tags=[],
        badges=[],
        kleo_points=0,
        settings={},
        first_time_user=True,
        total_data_quantity=0,
        activity_json={},
        milestones={
            "tweet_activity_graph": False,  # Boolean, true if milestone completed
            "data_owned": 0,  # Integer, MB of data owned
            "referred_count": 0,  # Integer, number of friends referred
            "followed_on_twitter": False,  # Boolean, true if followed on Twitter
        },
        referrals=[],  # List of users referred by this user
        referee=None,  # Who referred this user
        pii_removed_count=0,
    ):

        # Type assertions for validation
        assert isinstance(address, str)
        assert isinstance(slug, str)
        assert isinstance(stage, int)
        assert isinstance(name, str)
        assert isinstance(verified, bool)
        assert isinstance(last_cards_marked, int)
        assert isinstance(about, str)
        assert isinstance(pfp, str)
        assert isinstance(content_tags, list)
        assert isinstance(last_attested, int)
        assert isinstance(identity_tags, list)
        assert isinstance(badges, list)
        assert isinstance(kleo_points, int)
        assert isinstance(settings, dict)
        assert isinstance(first_time_user, bool)
        assert isinstance(total_data_quantity, int)
        assert isinstance(milestones, dict)
        assert isinstance(referrals, list)
        assert referee is None or isinstance(referee, str)
        assert isinstance(pii_removed_count, int)

        self.document = {
            "address": address,
            "slug": slug,
            "name": name,
            "stage": stage,
            "verified": verified,
            "last_cards_marked": last_cards_marked,
            "about": about,
            "pfp": pfp,
            "content_tags": content_tags,
            "last_attested": last_attested,
            "identity_tags": identity_tags,
            "badges": badges,
            "kleo_points": kleo_points,
            "settings": settings,
            "first_time_user": first_time_user,
            "total_data_quantity": total_data_quantity,
            "milestones": milestones,
            "referrals": referrals,  # Track users referred by this user
            "referee": referee,  # Track who referred this user
            "pii_removed_count": pii_removed_count,
        }

    def save(self, signup):
        existing_user_address = find_by_address(self.document["address"])
        if existing_user_address:
            return existing_user_address
        else:
            user_collection.insert_one(self.document)
        return self.document


def get_activity_json(address):
    try:
        # Find the user by address
        user = db.users.find_one(
            {"address": address},
            {"_id": 0, "activity_json": 1},  # Exclude _id, include only previous_hash
        )

        if user:
            return user.get(
                "activity_json", ""
            )  # Return previous_hash if it exists, empty string otherwise
        else:
            return {}  # Return None if user not found

    except Exception as e:
        print(f"An error occurred while retrieving previous hash: {e}")
        return None


def update_activity_json(address, new_activity_json):
    try:
        filter_query = {"address": address}
        update_operation = {"$set": {"activity_json": new_activity_json}}

        user_of_db = db.users.find_one_and_update(
            filter_query,
            update_operation,
            projection={"_id": 0},
            return_document=pymongo.ReturnDocument.AFTER,
        )

        return user_of_db
    except StopIteration as _:
        return None

    except Exception as e:
        return {}


def update_previous_hash(address, new_hash):
    try:
        filter_query = {"address": address}
        update_operation = {"$set": {"previous_hash": new_hash}}

        user_of_db = db.users.find_one_and_update(
            filter_query,
            update_operation,
            projection={"_id": 0},
            return_document=pymongo.ReturnDocument.AFTER,
        )

        return user_of_db

    # TODO: Error Handling
    # If an invalid ID is passed to `get_movie`, it should return None.
    except StopIteration as _:
        return None

    except Exception as e:
        return {}


def find_by_address(address):
    try:
        pipeline = [
            {"$match": {"$expr": {"$eq": [{"$toLower": "$address"}, address.lower()]}}},
            {"$project": {"_id": 0}},
        ]
        user_of_db = db.users.aggregate(pipeline).next()
        return user_of_db
    except StopIteration as _:
        return None
    except Exception as e:
        return {}

# Updates the PIIRemovedCount and TotalDataContributed Size in DB for an User.
def update_user_data_by_address(address, pii_count, text_size):
    try:
        # First, retrieve the current total_data_quantity value for this user
        user = db.users.find_one({"address": address}, {"total_data_quantity": 1})
        if not user:
            print(f"User with address {address} not found.")
            return None

        # Calculate the new total_data_quantity
        current_total_data_quantity = user.get("total_data_quantity", 0)
        new_total_data_quantity = current_total_data_quantity + text_size

        # Now perform the update
        filter_query = {"address": address}
        update_operation = {
            "$inc": {
                "pii_removed_count": pii_count,  # Increment pii_removed_count
            },
            "$set": {
                "total_data_quantity": new_total_data_quantity,  # Update total_data_quantity
                "milestones.data_owned": new_total_data_quantity,  # Sync milestones.data_owned with total_data_quantity
            },
        }
        user_of_db = db.users.find_one_and_update(
            filter_query,
            update_operation,
            projection={"_id": 0},
            return_document=pymongo.ReturnDocument.AFTER,
        )
        return user_of_db

    except Exception as e:
        print(f"An error occurred while updating user data: {e}")
        return None


# Admin can update the mileStones.
def update_user_milestones_data_by_address(address, milestones, kleo_points):
    try:
        filter_query = {"address": address}
        update_operation = {
            "$set": {
                "milestones": milestones,
                "kleo_points": kleo_points,
            }
        }
        user_of_db = db.users.find_one_and_update(
            filter_query,
            update_operation,
            projection={"_id": 0},
            return_document=pymongo.ReturnDocument.AFTER,
        )
        return user_of_db

    except Exception as e:
        print(f"An error occurred while updating user data: {e}")
        return None


# Get top N users based on KleoPoints. Leaderboard.
def get_top_users_by_kleo_points(limit=10):
    try:
        # Fetch users sorted by Kleo points in descending order, limit the result to `limit`
        users = list(
            db.users.find(
                {},  # No filter, fetch all users
                {
                    "_id": 0,  # Exclude `_id`
                    "address": 1,  # Include `address`
                    "kleo_points": 1,  # Include `kleo_points`
                },
            )
            .sort(
                "kleo_points", pymongo.DESCENDING
            )  # Sort by `kleo_points` in descending order
            .limit(limit)  # Limit the number of results to `limit`
        )

        # Format the result
        leaderboard = []
        for index, user in enumerate(users, start=1):
            leaderboard.append(
                {
                    "rank": index,  # Rank starts from 1
                    "address": user["address"],  # Include user's address
                    "kleo_points": user.get("kleo_points", 0),  # Include kleo_points
                }
            )

        return leaderboard
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


# Calculate the user's rank based on their Kleo points compared to other users.
def calculate_rank(address):
    try:
        # First, get the user's Kleo points by address
        user = db.users.find_one({"address": address}, {"kleo_points": 1, "_id": 0})
        if not user:
            return {"error": "User not found"}, 404

        user_kleo_points = user.get("kleo_points", 0)

        # Count how many users have more Kleo points
        higher_ranked_users = db.users.count_documents(
            {"kleo_points": {"$gt": user_kleo_points}}
        )

        # The rank is the number of users with more points, plus one
        rank = higher_ranked_users + 1

        # Get total number of users
        total_users = db.users.count_documents({})

        return {
            "address": address,
            "kleo_points": user_kleo_points,
            "rank": rank,
            "total_users": total_users,
        }

    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error": "An error occurred while calculating rank"}, 500


def get_previous_hash(address):
    try:
        # Find the user by address
        user = db.users.find_one(
            {"address": address},
            {"_id": 0, "previous_hash": 1},  # Exclude _id, include only previous_hash
        )

        if user:
            return user.get(
                "previous_hash", ""
            )  # Return previous_hash if it exists, empty string otherwise
        else:
            return None  # Return None if user not found

    except Exception as e:
        print(f"An error occurred while retrieving previous hash: {e}")
        return None


# Finds a user and returns the referrals object for that user, including their kleo points.
def fetch_users_referrals(address):
    try:
        # First, get the user's details by address
        user = db.users.find_one({"address": address})
        if not user:
            return {"error": "User not found"}, 404

        # Get the referrals list
        referrals = user.get("referrals", [])
        if not referrals:
            return []

        # Initialize a list to store referral details
        referral_details = []

        # Iterate through each referral and get their kleo_points
        for referral in referrals:
            referred_user = db.users.find_one(
                {"address": referral["address"]}, {"kleo_points": 1, "_id": 0}
            )

            # Extract kleo_points if user is found, otherwise default to 0
            kleo_points = referred_user.get("kleo_points", 0) if referred_user else 0

            # Append the referral data along with kleo_points
            referral_details.append(
                {
                    "address": referral["address"],
                    "joining_date": referral["joining_date"],
                    "kleo_points": kleo_points,
                }
            )

        return referral_details

    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error": "An error occurred while fetching referrals."}, 500


def update_referee_and_bonus(user_address, referee_address):
    """
    Updates the user's referee information and assigns the referral bonus.
    """
    try:
        # Get the current timestamp in milliseconds for the joining date
        current_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

        # Add the referee to the user's record
        db.users.update_one(
            {"address": user_address}, {"$set": {"referee": referee_address}}
        )
        referral_bonus = 100

        # Update the kleo_points for both the referee and the referred user
        db.users.update_one(
            {"address": referee_address},
            {
                "$inc": {
                    "kleo_points": referral_bonus,
                    "milestones.referred_count": 1,  # Increment referred_count by 1
                },
                "$push": {
                    "referrals": {
                        "address": user_address,
                        "joining_date": {"$numberLong": str(current_timestamp)},
                    }
                },
            },
        )
        # db.users.update_one(
        #     {"address": user_address},
        #     {"$inc": {"kleo_points": referral_bonus}}
        # )

        # print(
        #     f"Assigned referee {referee_address} to user {user_address}, added bonus, and updated referrals."
        # )
    except Exception as e:
        print(f"An error occurred while updating referral: {e}")