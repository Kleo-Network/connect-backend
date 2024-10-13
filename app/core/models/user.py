import pymongo
from datetime import datetime
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


def set_signup_upload_by_slug(slug):
    try:
        filter_query = {"slug": slug}
        update_operation = {"$set": {"first_time_user": False}}
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
        print(e)
        return {}


def find_by_slug(slug):
    try:
        pipeline = [
            {"$match": {"slug": slug}},
            {"$project": {"_id": 0, "address": 0}},  # Exclude the _id field
        ]
        user_of_db = db.users.aggregate(pipeline).next()
        return user_of_db

    # TODO: Error Handling
    # If an invalid ID is passed to `get_movie`, it should return None.
    except StopIteration as _:
        return None

    except Exception as e:
        return {}


def find_by_address_slug_first_time(slug):
    try:
        pipeline = [{"$match": {"slug": slug}}]
        user_of_db = db.users.aggregate(pipeline).next()
        return user_of_db.get("address", "0x"), user_of_db.get("first_time_user", False)
    except StopIteration as _:
        return None


def find_by_address_slug(slug):
    try:
        pipeline = [{"$match": {"slug": slug}}]
        user_of_db = db.users.aggregate(pipeline).next()
        return user_of_db["address"]

    # TODO: Error Handling
    # If an invalid ID is passed to `get_movie`, it should return None.
    except StopIteration as _:
        return None

    except Exception as e:
        return {}


def find_by_address(address):
    try:
        pipeline = [
            {"$match": {"address": address}},
            {"$project": {"_id": 0, "address": 0}},  # Exclude the _id field
        ]
        user_of_db = db.users.aggregate(pipeline).next()
        return user_of_db

    # TODO: Error Handling
    # If an invalid ID is passed to `get_movie`, it should return None.
    except StopIteration as _:
        return None

    except Exception as e:
        return {}


def update_by_slug(
    address,
    slug,
    stage,
    name="",
    verified=False,
    about="",
    pfp="",
    content_tags=[],
    identity_tags=[],
    badges=[],
    profile_metadata={},
):
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
                "profile_metadata": profile_metadata,
            }
        }
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
        print(e)
        return {}


def update_settings_by_slug(slug, settings, stage, about):
    try:
        filter_query = {"slug": slug}
        update_operation = {
            "$set": {"settings": settings, "stage": stage, "about": about}
        }
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
        print(e)
        return {}


def fetch_user_slug():
    slug_from_db = db.users.find({}, {"slug": 1})
    user_slugs = [user["slug"] for user in slug_from_db if "slug" in user]
    return user_slugs


def update_last_cards_marked(slug):
    try:
        db.users.update_one(
            {"slug": slug},
            {"$set": {"last_cards_marked": int(datetime.now().timestamp())}},
        )

    # TODO: Error Handling
    # If an invalid ID is passed to `get_movie`, it should return None.
    except StopIteration as _:
        return None

    except Exception as e:
        print(e)
        return {}


def update_last_attested(slug):
    try:
        db.users.update_one(
            {"slug": slug}, {"$set": {"last_attested": int(datetime.now().timestamp())}}
        )
    except Exception as e:
        print(e)
        return {}


def update_minting_count(slug):
    try:
        pipeline = [{"$match": {"slug": slug}}]

        # Execute the pipeline and get the user
        cursor = db.users.aggregate(pipeline)
        user = next(cursor, None)

        if user:
            user_profile_metadata = user.get("profile_metadata", {})
            mint_count = user_profile_metadata.get("mint_count", 0)
            kleo_token = user_profile_metadata.get("kleo_token", 0)
            tobe_release_tokens = user_profile_metadata.get("tobe_release_tokens", 0)

            if user_profile_metadata and mint_count:
                mint_count_updated = int(mint_count) + 1
                user_profile_metadata["mint_count"] = mint_count_updated
            else:
                user_profile_metadata["mint_count"] = 1

            if user_profile_metadata and tobe_release_tokens:
                if kleo_token:
                    user_profile_metadata["kleo_token"] = (
                        kleo_token + tobe_release_tokens
                    )
                else:
                    user_profile_metadata["kleo_token"] = tobe_release_tokens
                user_profile_metadata["tobe_release_tokens"] = 0
            else:
                if not kleo_token:
                    user_profile_metadata["kleo_token"] = 1

            db.users.update_one(
                {"slug": slug}, {"$set": {"profile_metadata": user_profile_metadata}}
            )
    except Exception as e:
        print(e)
        return {}


def update_tobe_release_kleo_token(slug):
    try:
        pipeline = [{"$match": {"slug": slug}}]

        # Execute the pipeline and get the user
        cursor = db.users.aggregate(pipeline)
        user = next(cursor, None)

        if user:
            user_profile_metadata = user.get("profile_metadata", {})
            tobe_release_tokens = user_profile_metadata.get("tobe_release_tokens", 0)

            if user_profile_metadata and tobe_release_tokens:
                updated_tobe_release_tokens = int(tobe_release_tokens) + 1
                user_profile_metadata["tobe_release_tokens"] = (
                    updated_tobe_release_tokens
                )
            else:
                user_profile_metadata["tobe_release_tokens"] = 1
            db.users.update_one(
                {"slug": slug}, {"$set": {"profile_metadata": user_profile_metadata}}
            )
    except Exception as e:
        print(e)
        return {}


def update_about_by_slug(slug, about):
    try:
        filter_query = {"slug": slug}
        update_operation = {"$set": {"about": about}}
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
        print(e)
        return {}


def get_all_users_with_count():
    try:
        users = list(db.users.find({}, {"_id": 0}))
        return users
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


def update_kleo_points_for_user(slug):
    try:
        pipeline = [{"$match": {"slug": slug}}]

        # Execute the pipeline and get the user
        cursor = db.users.aggregate(pipeline)
        user = next(cursor, None)

        if user:
            user_profile_metadata = user.get("profile_metadata", {})
            kleo_points_for_user = user_profile_metadata.get("kleo_points", 0)
            kleo_token_of_user = user_profile_metadata.get("kleo_token", 0)
            tobe_released_token_of_user = user_profile_metadata.get(
                "tobe_release_tokens", 0
            )

            if user_profile_metadata and kleo_points_for_user:
                updated_kleo_points = int(kleo_points_for_user) + 1
                user_profile_metadata["kleo_points"] = updated_kleo_points
            else:
                user_profile_metadata["kleo_points"] = (
                    int(kleo_token_of_user) + int(tobe_released_token_of_user) + 1
                )
            db.users.update_one(
                {"slug": slug}, {"$set": {"profile_metadata": user_profile_metadata}}
            )
    except Exception as e:
        print(e)
        return {}


def get_top_users_by_kleo_points(limit=20):
    try:
        # Fetch users and sort them by Kleo points in descending order
        users = list(
            db.users.find(
                {}, {"_id": 0, "slug": 1, "name": 1, "profile_metadata.kleo_points": 1}
            )
            .sort("profile_metadata.kleo_points", pymongo.DESCENDING)
            .limit(limit)
        )

        # Format the result
        leaderboard = []
        for index, user in enumerate(users, start=1):
            leaderboard.append(
                {
                    "rank": index,
                    "slug": user["slug"],
                    "name": user.get("name", "Anonymous"),
                    "kleo_points": user.get("profile_metadata", {}).get(
                        "kleo_points", 0
                    ),
                }
            )

        return leaderboard
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


def calculate_rank(slug):
    try:
        # First, get the user's Kleo points
        user = db.users.find_one(
            {"slug": slug}, {"profile_metadata.kleo_points": 1, "_id": 0}
        )
        if not user:
            return {"error": "User not found"}, 404

        user_kleo_points = user.get("profile_metadata", {}).get("kleo_points", 0)

        # Count how many users have more Kleo points
        higher_ranked_users = db.users.count_documents(
            {"profile_metadata.kleo_points": {"$gt": user_kleo_points}}
        )

        # The rank is the number of users with more points, plus one
        rank = higher_ranked_users + 1

        # Get total number of users
        total_users = db.users.count_documents({})

        return {
            "slug": slug,
            "kleo_points": user_kleo_points,
            "rank": rank,
            "total_users": total_users,
        }, 200

    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error": "An error occurred while calculating rank"}, 500


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
