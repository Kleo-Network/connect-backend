from flask import Blueprint, request, jsonify
from ..models.user import User, find_by_address
from ..modules.auth import get_jwt_token
import os
import requests

core = Blueprint('core', __name__)

@core.route('/create-user', methods=["POST"])
def create_user():
    vana_project_name = os.environ.get('VANA_PROJECT_NAME')
    vana_api_key = os.environ.get('VANA_API_KEY')
    data = request.get_json()
    walletAddress = data.get("walletAddress")

    user = find_by_address(walletAddress)

    if user:
        return jsonify({'error': 'Please login to your account'}), 400
    else:
        user = User(walletAddress, walletAddress, 1)
        response = user.save(True)
        response['token'] = get_jwt_token(walletAddress, walletAddress)

        headers = {
            'Authorization': f'Bearer {vana_api_key}'
        } 

        vana_api_url = f"https://www.vanadatahero.com/api/integrations/{vana_project_name}/deposit"

        vana_payload = {
            "walletAddress": walletAddress
        }

        try:
            response_from_vana = requests.post(vana_api_url, json=vana_payload,  headers=headers)
            response['vana_response_status_code'] = response_from_vana.status_code
        except Exception as e:
            print(f"Failed to allocate vana points to address: {walletAddress}. Error: {str(e)}")
        
    return response, 200
    

