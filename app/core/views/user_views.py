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

@core.route('/get-user/<string:slug>', methods=["GET"])
@token_required
def get_mongo_user(slug, **kwargs):
    if not all([slug]):
        return jsonify({"error": "Missing required parameters"}), 400
    address = find_by_slug(slug)['address']
    address_from_token = kwargs.get('user_data')['payload']['publicAddress']
    if not check_user_authenticity(address, address_from_token):
        return jsonify({"error": "user is not authorised"}), 401
    response = find_by_slug(slug)
    return jsonify(response), 200


@core.route('/create-user', methods=["POST"])
def create_user():
    data = request.get_json()
    address = data.get("address")
    signup = data.get("signup", False)
    stage = data.get("stage")
    slug = data.get("slug")
    name = data.get("name")
    pfp = data.get("pfp")

    if not all([address, stage, slug, name, pfp]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    user = User(address, slug, stage, name, pfp)
    response = user.save(signup)
    if not response:
        return jsonify({"404": "User not found"}),404
    else:
        return response, 200
       

@core.route('/update-user/<string:slug>', methods=["PUT"])
@token_required
def update_user(slug, **kwargs):
    data = request.get_json()
    name = data.get("name")
    verified = data.get("verified")
    about = data.get("about")
    pfp = data.get("pfp")
    content_tags = data.get("content_tags")
    identity_tags = data.get("identity_tags")
    badges = data.get("badges")
    profile_metadata = data.get("profile_metadata")
    
    if not all([address, name, slug, about, pfp, content_tags, identity_tags, badges, profile_metadata]):
        return jsonify({"error": f"Missing required parameters"}), 400
    
    address = find_by_slug(slug).address
    address_from_token = kwargs.get('user_data')['payload']['publicAddress']
    if not check_user_authenticity(address, address_from_token):
        return jsonify({"error": "user is not authorised"}), 401
    
    response = update_by_slug(address, slug, name, verified, about, pfp, content_tags, identity_tags, badges, profile_metadata)
    return jsonify(response), 200

@core.route('/update-settings/<string:slug>', methods = ['PUT'])
@token_required
def update_user_settings(slug, **kwargs):
    data = request.get_json()
    settings = data.get("settings")
    stage = data.get("stage")
    about = data.get("about")
    
    address = find_by_slug(slug)['address']
    if not all([slug, settings, stage]):
            return jsonify({"error": f"Missing required parameters"}), 400
        
    address_from_token = kwargs.get('user_data')['payload']['publicAddress']
    if not check_user_authenticity(address, address_from_token):
        return jsonify({"error": "user is not authorised"}), 401  
    
    response = update_settings_by_slug(slug, settings, stage, about)
    return jsonify(response), 200

@core.route('/<string:slug>/published-cards/info', methods=["GET"])
def get_user_and_card_detail(slug):
    if not slug:
        return jsonify({"error": f"Missing required parameters"}), 400
    
    user = find_by_slug(slug)
    cards = get_published_card(slug)
    response = {
        "user": user,
        "published_cards": cards
    }
    return jsonify(response), 200

@core.route('/check_slug', methods=['GET'])
def check_slug():
    data = request.get_json()
    slug = data.get("slug")
    if not slug:
        return jsonify({'error': 'Slug parameter is missing.'}), 400
    slugs = fetch_user_slug()
    if slug in slugs:
        return jsonify({'result': False}), 200
    else:
        return jsonify({'result': True}), 200

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

       
