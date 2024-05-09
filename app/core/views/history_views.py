from flask import Blueprint, current_app, request
from ..controllers.history import *
from werkzeug.local import LocalProxy
from ...celery.tasks import *
from math import ceil
from celery import chord, group
from .auth_views import token_required
from flask import jsonify

core = Blueprint('core', __name__)

logger = LocalProxy(lambda: current_app.logger)


@core.before_request
def before_request_func():
    current_app.logger.name = 'core'
    
@core.route('/upload', methods=['POST'])
@token_required
def upload(**kwargs):
    data = request.get_json()
    history = data["history"]
    slug = data["slug"]
    
    if not all([slug, history]):
        return jsonify({"error": f"Missing required parameters"}), 400
    
    address, signup = find_by_address_slug(slug)
    if not address:
        return jsonify({"error": "user is not found"}), 401
        
    address_from_token = kwargs.get('user_data')['payload']['publicAddress']
    if not check_user_authenticity(address, address_from_token):
       return jsonify({"error": "user is not authorised"}), 401
    
    chunks = [history[i:i + 50] for i in range(0, len(history), 50)]
    categorize_tasks = [categorize_history.s({"chunk": chunk, "slug": slug}) for chunk in chunks]
    
    if signup:
        callback = create_pending_card.s(slug)
        chord(categorize_tasks)(callback)
    else:
        group(categorize_tasks).apply_async()
    
    
    return 'History Upload and Categorization is queued!'