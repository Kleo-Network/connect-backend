from flask import Blueprint, request, jsonify
import random
from app.celery.userDataComputation.activityClassification import (
    get_most_relevant_activity,
)
from app.core.modules.activity_chart import upload_image_to_imgur
from ..models.user import User, find_by_address
from ..modules.auth import get_jwt_token
import os
import requests
from ...celery.tasks import *
from ..models.history import get_top_activities, get_history_count

core = Blueprint("core", __name__)


@core.route("/get-user-graph/<userAddress>", methods=["GET"])
def get_user_graph(userAddress):
    try:
        print(userAddress)
        count_user = get_history_count(userAddress)
        print(count_user)
        if count_user < 10:
            return jsonify({"processing": True}), 200
            
        if not userAddress:
            return jsonify({"error": "Address is required"}), 400
        top_activities = get_top_activities(userAddress)

        if not top_activities:
            return jsonify({"error": "No activity data found"}), 404

        return jsonify({"data": top_activities}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@core.route("/save-history", methods=["POST"])
def save_history():
    data = request.get_json()
    user_address = data.get("address")
    print(user_address)
    print(data.get("signup"))
    history = data.get("history")
    for item in history:
        task = contextual_activity_classification.delay(item, user_address)

    # THIS IS JSON OF ITEM
    # {'id': '16132', 'url': 'https://www.google.com/search?q=imgflip&oq=imgflip&gs_lcrp=EgZjaHJvbWUyDAgAEEUYORixAxiABDIHCAEQABiABDIHCAIQABiABDIHCAMQABiABDIHCAQQABiABDIHCAUQABiABDIHCAYQABiABDIHCAcQABiABDIHCAgQABiABNIBCDE1MDRqMGo3qAIAsAIA&sourceid=chrome&ie=UTF-8', 'title': 'imgflip - Google Search', 'lastVisitTime': 1727571259983.67, 'visitCount': 2, 'typedCount': 0}
    return jsonify({"data": True}), 200


@core.route("/create-user", methods=["POST"])
def create_user():
    """
    Create a new user or return existing user information.
    If the user exists, return their data along with a JWT token.
    If the user doesn't exist, create a new user, allocate Vana points and tokens,
    and generate a 5-digit random code.
    """
    data = request.get_json()

    print("data", data.get("address"))
    wallet_address = data.get("address")

    user = find_by_address(wallet_address)

    if user:
        user["token"] = get_jwt_token(wallet_address, wallet_address)
        return jsonify(user), 200

    # Generate a 5-digit random code
    random_code = str(random.randint(100, 9999999))

    # Create a new user with the random code
    user = User(address=wallet_address, slug=random_code)
    response = user.save(signup=True)

    # Prepare the response object
    user_data = {
        "password": response["slug"],
        "token": get_jwt_token(wallet_address, wallet_address),
    }
    print(jsonify(user_data))
    return jsonify(user_data), 200  # 201 Created


@core.route("/upload_activity_chart", methods=["POST"])
def upload_activity_chart():
    try:
        # Retrieve base64 image data from the POST request body
        image_data = request.json.get("image")

        if not image_data:
            return jsonify({"error": "No image data provided"}), 400

        # Call the upload service to upload the image to Imgur
        image_url = upload_image_to_imgur(image_data)

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
