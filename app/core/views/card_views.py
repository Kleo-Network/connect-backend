from flask import Blueprint, current_app, request, jsonify
from ..controllers.user import *
from werkzeug.local import LocalProxy
from ..controllers.user import * 
core = Blueprint('core', __name__)
from .auth_views import *
from ..controllers.checks import * 
from ..models.pending_cards import *
from ..models.published_cards import *
from ..models.static_cards import *
from bson.objectid import ObjectId

logger = LocalProxy(lambda: current_app.logger)

@core.route('/pending/<string:slug>', methods=["GET"])
def get_pending_cards(slug):
    if not all([slug]):
        return jsonify({"error": "Missing required parameters"}), 400
            
    response = get_pending_card(slug)
    return jsonify(response), 200

@core.route('/pending/<string:slug>', methods=["DELETE"])
@token_required
def delete_pending_cards(slug,**kwargs):
    data = request.get_json()
    ids_of_card = data.get("ids")
    if not all([slug, ids_of_card]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    address = find_by_slug(slug)['address']
    address_from_token = kwargs.get('user_data')['payload']['publicAddress']
    if not check_user_authenticity(address, address_from_token):
        return jsonify({"error": "user is not authorised"}), 401
    
    ids = [ObjectId(id) for id in ids_of_card]
    result = delete_pending_card(slug, ids)
    return result

@core.route('/published/<string:slug>', methods=["GET"])
def get_published_cards(slug):
    if not all([slug]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    response = get_published_card(slug)
    return jsonify(response), 200

@core.route('/published/<string:slug>', methods=["DELETE"])
@token_required
def delete_published_cards(slug, **kwargs):
    data = request.get_json()
    ids_of_card = data.get("ids")
    if not all([slug, ids_of_card]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    address = find_by_slug(slug)['address']
    address_from_token = kwargs.get('user_data')['payload']['publicAddress']
    if not check_user_authenticity(address, address_from_token):
        return jsonify({"error": "user is not authorised"}), 401
    
    ids = [ObjectId(id) for id in ids_of_card]
    result = delete_published_card(slug, ids)
    return result

@core.route('/static/<string:address>', methods=["GET"])
def get_static_cards(address):
    if not all([address]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    response = get_static_card(address)
    return jsonify(response), 200

@core.route('/static/<string:slug>', methods=['POST'])
def create_static_cards(slug):
    try:
        # Get JSON data from request body
        data = request.get_json()
        cards_data = data.get("cards")
        
        if not all([slug, cards_data]):
            return jsonify({"error": "Missing required parameters"}), 400
        
        if not isinstance(cards_data, list):
            return jsonify({"error": "Invalid JSON data. Expected a list of objects."}), 400
        
        for card in cards_data:
            type = card.get('type')
            metadata = card.get('metadata', {})
            
            # Create StaticCards instance and save to database
            static_card = StaticCards(slug, type, int(datetime.now().timestamp()), metadata)
            static_card.save()
        
        return jsonify({"message": "All documents saved successfully"}), 201
    
    except Exception as e:
        print(e)
        return jsonify({"error": "error while creating static card"}), 500
    
@core.route('/static/<string:slug>', methods=['PUT'])
def update_static_cards(slug):
    try:
        data = request.get_json()
        type = data.get("type")
        metadata = data.get("metadata")
        
        if not all([slug, type, metadata]):
            return jsonify({"error": "Missing required parameters"}), 400
        
        response = update_static_card(slug, type, metadata)
        return jsonify(response), 200
        
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500