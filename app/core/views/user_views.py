from flask import Blueprint, current_app, request
from ..models.user import *
from werkzeug.local import LocalProxy

core = Blueprint('core', __name__)

logger = LocalProxy(lambda: current_app.logger)

@core.route('/get_profile_info', methods=["GET"])
def get_profile_information():
    user_id = request.args.get('user_id')
    response = get_entire_profile(user_id)
    return response
