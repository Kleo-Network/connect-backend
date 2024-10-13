import pymongo
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# MongoDB connection URI
mongo_uri = os.environ.get("DB_URL")
db_name = os.environ.get("DB_NAME")

# Connect to MongoDB
client = pymongo.MongoClient(mongo_uri)
db = client[db_name]
user_collection = db["users"]

# New fields with default values including milestones
default_values = {
    "stage": 1,
    "name": "",
    "pfp": "",
    "verified": False,
    "last_cards_marked": 0,
    "about": "",
    "content_tags": [],
    "last_attested": 0,
    "identity_tags": [],
    "badges": [],
    "kleo_points": 0,
    "settings": {},
    "first_time_user": True,
    "total_data_quantity": 0,
    "milestones": {
        "tweet_activity_graph": False,  # Boolean
        "data_owned": 0,  # Integer
        "referred_count": 0,  # Integer
        "followed_on_twitter": False,  # Boolean
    },
    "referrals": [],
    "referee": None,
    "pii_removed_count": 0,
}


# Update each user document
def update_user_documents():
    try:
        logging.info("Starting the update process...")

        # Fetch all users from the collection
        users = user_collection.find({})
        user_count = user_collection.count_documents({})
        logging.info(f"Found {user_count} users in the database.")

        for i, user in enumerate(users, start=1):
            logging.info(
                f"Processing user {i}/{user_count}: {user.get('address', 'unknown')}"
            )

            # Prepare update document with default values
            update_doc = default_values.copy()

            # Check if 'kleo_points' should come from 'profile_metadata.kleo_points'
            if "profile_metadata" in user and "kleo_points" in user["profile_metadata"]:
                update_doc["kleo_points"] = user["profile_metadata"]["kleo_points"]
                logging.info(
                    f"User {user.get('address')} has kleo_points from profile_metadata: {update_doc['kleo_points']}"
                )
            else:
                update_doc["kleo_points"] = default_values["kleo_points"]
                logging.info(
                    f"User {user.get('address')} does not have kleo_points in profile_metadata, using default: {update_doc['kleo_points']}"
                )

            # Apply only if fields are missing in the document
            for key, value in default_values.items():
                if key not in user:
                    update_doc[key] = value

            # Update the user document in MongoDB, preserving existing fields
            result = user_collection.update_one(
                {"_id": user["_id"]}, {"$set": update_doc}
            )

            if result.modified_count > 0:
                logging.info(f"User {user.get('address')} updated successfully.")
            else:
                logging.info(
                    f"No changes were necessary for user {user.get('address')}."
                )

        logging.info("All users have been updated successfully.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")


# Run the update function
if __name__ == "__main__":
    update_user_documents()
