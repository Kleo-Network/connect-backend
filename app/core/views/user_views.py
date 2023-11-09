from flask import Blueprint, current_app, request
from ..controllers.user import *
from werkzeug.local import LocalProxy
from .auth_views import *
core = Blueprint('core', __name__)

logger = LocalProxy(lambda: current_app.logger)

@core.route('/get_profile_info', methods=["GET"])
@token_required
def get_user_data(current_user_id):
    data = request.json
    payload_user_id = data.get('address')
    if payload_user_id != current_user_id:
        return jsonify({'message': 'Unauthorized access to this resource.'}), 403
    return jsonify({'message': f'Access granted: {current_user_id}.'})
