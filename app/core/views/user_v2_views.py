from flask import Blueprint, request, jsonify
from ..models.user import User, find_by_address
from ..modules.auth import get_jwt_token
import os
import requests

core = Blueprint("core", __name__)


@core.route("/create-user", methods=["POST"])
def create_user():
    data = request.get_json()
    walletAddress = data.get("walletAddress")

    user = find_by_address(walletAddress)

    if user:
        user["address"] = walletAddress
        user["token"] = get_jwt_token(walletAddress, walletAddress)
        return user, 200
    else:
        user = User(walletAddress, walletAddress, 1)
        response = user.save(True)
        response["token"] = get_jwt_token(walletAddress, walletAddress)
        response["vana_point_allocation_response_status_code"] = allocate_vana_points(
            walletAddress
        )
        response["vana_token_allocation_hash"] = allocate_vana_tokens(walletAddress)

    return response, 200


def allocate_vana_points(walletAddress):
    vana_project_name = os.environ.get("VANA_PROJECT_NAME")
    vana_api_key = os.environ.get("VANA_API_KEY")

    headers = {"Authorization": f"Bearer {vana_api_key}"}

    vana_api_url = (
        f"https://www.vanadatahero.com/api/integrations/{vana_project_name}/deposit"
    )

    vana_payload = {"walletAddress": walletAddress}

    try:
        response_from_vana = requests.post(
            vana_api_url, json=vana_payload, headers=headers
        )
        return response_from_vana.status_code
    except Exception as e:
        print(
            f"Failed to allocate vana points to address: {walletAddress}. Error: {str(e)}"
        )
        return 500


def allocate_vana_tokens(walletAddress):
    vana_api_key = os.environ.get("VANA_API_KEY")

    headers = {"Authorization": f"Bearer {vana_api_key}"}

    vana_api_url = "https://faucet.vana.org/api/transactions"

    vana_payload_allocate_token = {"address": walletAddress}

    try:
        response_from_vana = requests.post(
            vana_api_url, json=vana_payload_allocate_token, headers=headers
        )
        return response_from_vana.json().get("hash") or response_from_vana.status_code
    except Exception as e:
        print(
            f"Failed to allocate vana token to address: {walletAddress}. Error: {str(e)}"
        )
        return 500
