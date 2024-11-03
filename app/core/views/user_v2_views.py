from flask import Blueprint, request, jsonify
import random

from app.core.modules.activity_chart import upload_image_to_image_bb
from ..models.user import *
from ..modules.auth import get_jwt_token
from ...celery.tasks import *
from ..models.history import get_top_activities, get_history_count
from ...core.models.constants import ABI, POLYGON_RPC

core = Blueprint("core", __name__)


@core.route("/get-user-graph/<userAddress>", methods=["GET"])
def get_user_graph(userAddress):
    try:
        if not userAddress:
            return jsonify({"error": "Address is required"}), 400

        cache_key = f"user_graph:{userAddress}"
        cached_data = redis_client.get(cache_key)

        if cached_data:
            data = json.loads(cached_data)
            response = jsonify({"data": data})
            response.status_code = 200
        else:
            response = jsonify({"processing": True})
            response.status_code = 200

        update_user_graph_cache.delay(userAddress)

        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@core.route("/save-history", methods=["POST"])
def save_history():
    data = request.get_json()
    # print(data)
    user_address = str(data.get("address")).lower()
    signup = data.get("signup")
    history = data.get("history")
    return_abi_contract = False
    user = find_by_address(user_address)

    try:
        if signup:
            referee_address = find_referral_in_history(history)
            if referee_address:
                update_referee_and_bonus(user_address, referee_address)
            contextual_activity_classification_for_batch.delay(history, user_address)
            return jsonify({"data": "Signup successful!"}), 200
        else:
            if get_history_count(user_address) > 50:
                return_abi_contract = True

            for item in history:
                if "content" in item:
                    user = find_by_address(user_address)
                    contextual_activity_classification.delay(item, user_address)

            if return_abi_contract:
                user = find_by_address(user_address)
                previous_hash = user.get("previous_hash", "first_hash")
                chain_data_list = [
                    {
                        "name": "polygon",
                        "rpc": POLYGON_RPC,
                        "contractData": {
                            "address": "0xD133A1aE09EAA45c51Daa898031c0037485347B0",
                            "abi": ABI,
                            "functionName": "safeMint",
                            "functionParams": [
                                user_address,
                                previous_hash,
                            ],
                        },
                    }
                ]

                response = {
                    "chains": chain_data_list,
                    "password": user.get("slug"),
                }

                return jsonify({"data": response}), 200
            return (
                jsonify({"status": "success", "message": "History saved successfully"}),
                200,
            )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



@core.route("/create-user", methods=["POST"])
def create_user():
    data = request.get_json()
    wallet_address = data.get("address")

    if not wallet_address:
        return jsonify({"error": "Address is required"}), 400

    user = find_by_address(wallet_address)
    if user:
        try:
            token = get_jwt_token(wallet_address, wallet_address)
        except Exception as e:
            return jsonify({'error': 'Failed to generate token'}), 500
        
        user_data = {"password": user["slug"], "token": token}
        return jsonify(user_data), 200

    random_code = str(random.randint(100, 9999999))

    user = User(address=wallet_address, slug=random_code)
    response = user.save(signup=True)

    try:
        token = get_jwt_token(wallet_address, wallet_address)
    except Exception as e:
        return jsonify({'error': 'Failed to generate token'}), 500

    user_data = {
        "password": response["slug"],
        "token": token,
    }
    print(user_data)
    return jsonify(user_data), 200



@core.route("/upload_activity_chart", methods=["POST"])
def upload_activity_chart():
    try:
        # Retrieve base64 image data from the POST request body
        image_data = request.json.get("image")

        if not image_data:
            return jsonify({"error": "No image data provided"}), 400

        # Call the upload function to upload the image to Imgbb
        image_url = upload_image_to_image_bb(image_data)

        if image_url:
            return jsonify({"url": image_url}), 200
        else:
            return jsonify({"error": "Image upload failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@core.route("/get-user/<userAddress>", methods=["GET"])
def get_user(userAddress):
    """
    Fetch user data from MongoDB based on the user's address.
    """
    try:
        # Query the MongoDB collection using the user's address
        user_data = find_by_address(userAddress)

        # If user data is not found, return a 404 error
        if not user_data:
            return jsonify({"error": "User not found"}), 404

        # Return the user data as JSON
        return jsonify(user_data), 200
    except Exception as e:
        # Handle any exceptions that occur and return a 500 error
        return jsonify({"error": str(e)}), 500


@core.route("/top-users", methods=["GET"])
def get_top_users():
    """Fetch the top users based on Kleo points and include the user's rank at the first index if the address is provided."""
    try:
        limit = request.args.get("limit", default=20, type=int)
        user_address = request.args.get("address", default=None, type=str)
        leaderboard = get_top_users_by_kleo_points(limit)

        # If user_address is provided, calculate the rank and add it at the first position
        if user_address:
            user_rank_data = calculate_rank(user_address)

            if user_rank_data:
                user_rank_entry = {
                    "address": user_rank_data["address"],
                    "kleo_points": user_rank_data["kleo_points"],
                    "rank": user_rank_data["rank"],
                }

                # Insert the user's rank at the first position
                leaderboard.insert(0, user_rank_entry)
            else:
                return (
                    jsonify(
                        {
                            "error": "Error fetching user's rank for address: {user_address}"
                        }
                    ),
                    500,
                )
        return jsonify(leaderboard), 200
    except Exception as e:
        return jsonify({"error": "An error occurred while fetching top users"}), 500


@core.route("/rank/<userAddress>", methods=["GET"])
def get_user_rank(userAddress):
    """Fetch the user's rank according to kleo_points"""
    try:
        rank = calculate_rank(userAddress)
        return rank
    except Exception as e:
        return jsonify({"error": "An error occurred while fetching user's rank"})


@core.route("/referrals/<userAddress>", methods=["GET"])
def get_user_referrals(userAddress):
    try:
        referrals = fetch_users_referrals(userAddress)
        return referrals
    except Exception as e:
        return jsonify({"error": "An error occurred while fetching user's referrals"})