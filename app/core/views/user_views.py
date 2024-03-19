from flask import Blueprint, current_app, request, jsonify
from ..controllers.user import *
from werkzeug.local import LocalProxy
from ..controllers.user import * 
core = Blueprint('core', __name__)
from .auth_views import *
from ..controllers.checks import * 
from ..models.user import *
from ..models.published_cards import get_published_card

logger = LocalProxy(lambda: current_app.logger)

@core.route('/get-user/<string:address>', methods=["GET"])
def get_mongo_user(address):
    if not all([address]):
        return jsonify({"error": "Missing required parameters"}), 400
            
    response = find_by_address(address)
    return jsonify(response), 200


@core.route('/create-user', methods=["POST"])
def create_user():
    data = request.get_json()
    address = data.get("address")
    signup = data.get("signup", False)

    if not all([address]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    user = User(address)
    response = user.save(signup)
    if not response:
        return jsonify({"404": "User not found"}),200
    else:
        return response, 200
       

@core.route('/update-user/<string:address>', methods=["PUT"])
def update_user(address):
    data = request.get_json()
    print(data)
    name = data.get("name")
    verified = data.get("verified")
    about = data.get("about")
    pfp = data.get("pfp")
    content_tags = data.get("content_tags")
    identity_tags = data.get("identity_tags")
    badges = data.get("badges")
    profile_metadata = data.get("profile_metadata")
    
    if not all([address, name, about, pfp, content_tags, identity_tags, badges, profile_metadata]):
        return jsonify({"error": f"Missing required parameters"}), 400
    
    response = update_by_address(address, name, verified, about, pfp, content_tags, identity_tags, badges, profile_metadata)
    return jsonify(response), 200

@core.route('/<string:address>/published-cards/info', methods=["GET"])
def get_user_and_card_detail(address):
    if not address:
        return jsonify({"error": f"Missing required parameters"}), 400
    
    user = find_by_address(address)
    cards = get_published_card(address)
    response = {
        "user": user,
        "published_cards": cards
    }
    return jsonify(response), 200

@core.route('/set_privacy', methods=["POST"])
def set_user_privacy():
    data = request.json
    user_id = data.get("user_id")
    privacy_settings = data.get("privacy")

    if not user_id or not privacy_settings:
        return jsonify({'error': 'Missing user_id or privacy settings'}), 400

    try:
        update_user_privacy(user_id, privacy_settings)
        return jsonify({'message': 'Privacy settings updated successfully'}), 200
    except Exception as e:
        print(f"Error updating privacy settings: {e}")
        return jsonify({'error': 'Failed to update privacy settings'}), 500

       
