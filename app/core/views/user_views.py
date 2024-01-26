from flask import Blueprint, current_app, request
from ..controllers.user import *
from werkzeug.local import LocalProxy
from ..controllers.user import * 
core = Blueprint('core', __name__)
from .auth_views import *
from ..controllers.checks import * 

logger = LocalProxy(lambda: current_app.logger)

@core.route('/create_user', methods=["POST"])
def create_user():
    data = request.json 
    id = data["address"]
    response = create_user_from_address(id)
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

       
