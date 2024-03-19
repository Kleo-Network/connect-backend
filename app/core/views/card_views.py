from flask import Blueprint, current_app, request, jsonify
from ..controllers.user import *
from werkzeug.local import LocalProxy
from ..controllers.user import * 
core = Blueprint('core', __name__)
from .auth_views import *
from ..controllers.checks import * 
from ..models.pending_cards import *
from ..models.published_cards import *
from bson.objectid import ObjectId

logger = LocalProxy(lambda: current_app.logger)

@core.route('/pending/<string:address>', methods=["GET"])
def get_pending_cards(address):
    if not all([address]):
        return jsonify({"error": "Missing required parameters"}), 400
            
    response = get_pending_card(address)
    return jsonify(response), 200

@core.route('/pending/<string:address>', methods=["DELETE"])
def delete_pending_cards(address):
    data = request.get_json()
    ids_of_card = data.get("ids")
    if not all([address, ids_of_card]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    ids = [ObjectId(id) for id in ids_of_card]
    result = delete_pending_card(address, ids)
    return result

@core.route('/published/<string:address>', methods=["GET"])
def get_published_cards(address):
    if not all([address]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    response = get_published_card(address)
    return jsonify(response), 200

@core.route('/published/<string:address>', methods=["DELETE"])
def delete_published_cards(address):
    data = request.get_json()
    ids_of_card = data.get("ids")
    if not all([address, ids_of_card]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    ids = [ObjectId(id) for id in ids_of_card]
    result = delete_published_card(address, ids)
    return result
