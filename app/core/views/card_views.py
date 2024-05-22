from flask import Blueprint, current_app, request, jsonify
from app.celery.tasks import force_create_pending_cards
from ..controllers.history import *
from werkzeug.local import LocalProxy
core = Blueprint('core', __name__)
from .auth_views import *
from ..models.pending_cards import *
from ..models.published_cards import *
from ..models.static_cards import *
from bson.objectid import ObjectId

logger = LocalProxy(lambda: current_app.logger)

@core.route('/pending/<string:slug>', methods=["GET"])
@token_required
def get_pending_cards(slug,**kwargs):
    if not all([slug]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    address = find_by_address_slug(slug)
    address_from_token = kwargs.get('user_data')['payload']['publicAddress']
    if not check_user_authenticity(address, address_from_token):
        return jsonify({"error": "user is not authorised"}), 401
            
    response = get_pending_card(slug)
    return jsonify(response), 200

@core.route('/pending/<string:slug>', methods=["DELETE"])
@token_required
def delete_pending_cards(slug,**kwargs):
    data = request.get_json()
    id = data.get("id")
    if not all([slug, id]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    address = find_by_address_slug(slug)
    address_from_token = kwargs.get('user_data')['payload']['publicAddress']
    if not check_user_authenticity(address, address_from_token):
        return jsonify({"error": "user is not authorised"}), 401
    
    result = delete_pending_card(slug, ObjectId(id))
    return result

@core.route('/published/<string:slug>', methods=["GET"])
@token_required
def get_published_cards(slug,**kwargs):
    if not all([slug]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    address = find_by_address_slug(slug)
    address_from_token = kwargs.get('user_data')['payload']['publicAddress']
    if not check_user_authenticity(address, address_from_token):
        return jsonify({"error": "user is not authorised"}), 401
    
    response = get_published_card(slug)
    return jsonify(response), 200

@core.route('/published/<string:slug>', methods=["DELETE"])
@token_required
def delete_published_cards(slug, **kwargs):
    data = request.get_json()
    id = data.get("id")
    if not all([slug, id]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    address = find_by_address_slug(slug)
    address_from_token = kwargs.get('user_data')['payload']['publicAddress']
    if not check_user_authenticity(address, address_from_token):
        return jsonify({"error": "user is not authorised"}), 401
    
    result = delete_published_card(slug, ObjectId(id))
    return result

@core.route('/published/<string:slug>', methods=["POST"])
@token_required
def populate_published_card(slug, **kwargs):
    try:
        data = request.get_json()
        id = data.get("id")
        is_publish_card = data.get("isPublishCard", False)
        if not all([slug, id]):
            return jsonify({"error": "Missing required parameters"}), 400
        
        address = find_by_address_slug(slug)
        if not address:
            return jsonify({"error": "user is not found"}), 401
        address_from_token = kwargs.get('user_data')['payload']['publicAddress']
        if not check_user_authenticity(address, address_from_token):
            return jsonify({"error": "user is not authorised"}), 401
        
        tobe_published_cards = get_pending_card(slug, ObjectId(id))
        
        if not tobe_published_cards:
            return jsonify({"message": f"No pending card found for {slug}"})
        
        tobe_published_card = tobe_published_cards[0]
        
        if is_publish_card:
            published_card = PublishedCard(slug, tobe_published_card['cardType'], tobe_published_card['content'], tobe_published_card['tags'], tobe_published_card['urls'], tobe_published_card['metadata'], tobe_published_card['category'], tobe_published_card['date'])
            published_card.save()
        delete = delete_pending_card(slug,ObjectId(id)) #We protect user privacy by deleting pending cards once we create published cards
        update_last_cards_marked(slug)
        
        return jsonify({"message": f"published card for {slug}"}), 200
    
    except Exception as e:
        print(e)
        return jsonify({"error": "error while creating published card"}), 500
    
@core.route('/mint/published/<string:slug>', methods=["PUT"])
@token_required
def mint_published_card(slug, **kwargs):
    try:
        address = find_by_address_slug(slug)
        if not address:
            return jsonify({"error": "user is not found"}), 401
        address_from_token = kwargs.get('user_data')['payload']['publicAddress']
        if not check_user_authenticity(address, address_from_token):
            return jsonify({"error": "user is not authorised"}), 401
        
        result = mint_cards(slug)
        update_last_attested(slug)
        return jsonify({'message': result}), 200
        
        
    except Exception as e:
        print(e)
        return jsonify({"error": f"error while marking published card as minted for {slug}"}), 500

@core.route('/static/<string:slug>', methods=["GET"])
@token_required
def get_static_cards(slug,**kwargs):
    if not all([slug]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    address = find_by_address_slug(slug)
    if not address:
        return jsonify({"error": "user is not found"}), 401
    address_from_token = kwargs.get('user_data')['payload']['publicAddress']
    if not check_user_authenticity(address, address_from_token):
        return jsonify({"error": "user is not authorised"}), 401
    
    response = get_static_card(slug)
    return jsonify(response), 200

@core.route('/static/<string:slug>', methods=['POST'])
@token_required
def create_static_cards(slug,**kwargs):
    try:
        # Get JSON data from request body
        data = request.get_json()
        cards_data = data.get("card")
        
        if not all([slug, cards_data]):
            return jsonify({"error": "Missing required parameters"}), 400
        
        if not isinstance(cards_data, dict):
            return jsonify({"error": "Invalid JSON data."}), 400
        
        address = find_by_address_slug(slug)
        if not address:
            return jsonify({"error": "user is not found"}), 401
        address_from_token = kwargs.get('user_data')['payload']['publicAddress']
        if not check_user_authenticity(address, address_from_token):
            return jsonify({"error": "user is not authorised"}), 401
        print(cards_data)
        type = cards_data.get('type')
        metadata = cards_data.get('metadata', {})
        print(metadata)
        
        # Create StaticCards instance and save to database
        static_card = StaticCards(slug, type, int(datetime.now().timestamp()), metadata)
        static_card.save()
        
        return jsonify({"message": "All documents saved successfully"}), 201
    
    except Exception as e:
        print(e)
        return jsonify({"error": "error while creating static card"}), 500
    
@core.route('/static/<string:slug>', methods=['PUT'])
@token_required
def update_static_cards(slug, **kwargs):
    try:
        data = request.get_json()
        type = data.get("type")
        metadata = data.get("metadata")
        
        if not all([slug, type, metadata]):
            return jsonify({"error": "Missing required parameters"}), 400
        
        address = find_by_address_slug(slug)
        if not address:
            return jsonify({"error": "user is not found"}), 401
        address_from_token = kwargs.get('user_data')['payload']['publicAddress']
        if not check_user_authenticity(address, address_from_token):
            return jsonify({"error": "user is not authorised"}), 401
        
        response = update_static_card(slug, type, metadata)
        return jsonify(response), 200
        
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500
    
@core.route('/update-cards', methods=["POST"])
def update_cards():
    data = request.get_json()
    slug = data.get('slug')
    password = data.get('password')
    if(password == os.environ.get("PASSWORD")):
        force_create_pending_cards.delay(slug)
        return jsonify({"message": "card created for the user"}), 200
    else:
        return jsonify({"error": "Please provide correct password"}), 500

# @core.route('/check-timed-tasks', methods=["GET"])
# def check_timed_tasks():
#     checking_next_task_schedule.delay()
#     return jsonify({"message": "hello world"}), 200