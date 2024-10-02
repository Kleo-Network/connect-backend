from flask import Blueprint, request, jsonify

from app.celery.userDataComputation.activityClassification import (
    get_most_relevant_activity,
)
from app.core.modules.activity_chart import upload_image_to_imgur
from ..models.user import User, find_by_address
from ..modules.auth import get_jwt_token
import os
import requests

core = Blueprint("core", __name__)


@core.route("/create-user", methods=["POST"])
def create_user():
    """
    Create a new user or return existing user information.
    If the user exists, return their data along with a JWT token.
    If the user doesn't exist, create a new user and allocate Vana points and tokens.
    """
    data = request.get_json()
    wallet_address = data.get("walletAddress")

    user = find_by_address(wallet_address)

    if user:
        user["token"] = get_jwt_token(wallet_address, wallet_address)
        return jsonify(user), 200

    # Create a new user
    user = User(wallet_address, wallet_address, 1)
    response = user.save(True)

    # Allocate Vana points and tokens
    response["token"] = get_jwt_token(wallet_address, wallet_address)
    response["vana_point_allocation_response_status_code"] = allocate_vana_points(
        wallet_address
    )
    response["vana_token_allocation_hash"] = allocate_vana_tokens(wallet_address)

    return jsonify(response), 201  # 201 Created


def allocate_vana_points(wallet_address):
    """
    Allocate Vana points to a user's wallet address.
    Returns the status code of the allocation response.
    """
    vana_project_name = os.environ.get("VANA_PROJECT_NAME")
    vana_api_key = os.environ.get("VANA_API_KEY")

    headers = {"Authorization": f"Bearer {vana_api_key}"}
    vana_api_url = (
        f"https://www.vanadatahero.com/api/integrations/{vana_project_name}/deposit"
    )
    vana_payload = {"walletAddress": wallet_address}

    try:
        response_from_vana = requests.post(
            vana_api_url, json=vana_payload, headers=headers
        )
        return response_from_vana.status_code
    except Exception as e:
        print(
            f"Failed to allocate Vana points to address: {wallet_address}. Error: {str(e)}"
        )
        return 500  # Internal Server Error


def allocate_vana_tokens(wallet_address):
    """
    Allocate Vana tokens to a user's wallet address.
    Returns the transaction hash or status code.
    """
    vana_api_key = os.environ.get("VANA_API_KEY")

    headers = {"Authorization": f"Bearer {vana_api_key}"}
    vana_api_url = "https://faucet.vana.org/api/transactions"
    vana_payload_allocate_token = {"address": wallet_address}

    try:
        response_from_vana = requests.post(
            vana_api_url, json=vana_payload_allocate_token, headers=headers
        )
        return response_from_vana.json().get("hash") or response_from_vana.status_code
    except Exception as e:
        print(
            f"Failed to allocate Vana token to address: {wallet_address}. Error: {str(e)}"
        )
        return 500  # Internal Server Error


@core.route("/activity_classification", methods=["POST"])
def classify_content():
    data = request.json

    activity = get_most_relevant_activity(data["content"])
    return jsonify(
        {"response": f"Most relevant activity for the content given is {activity}"}
    )


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
