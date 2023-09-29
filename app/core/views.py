
from flask import Blueprint, current_app, request
from werkzeug.local import LocalProxy

from authentication import require_appkey
from  .database import record_exists
from .tasks import categorize_history

core = Blueprint('core', __name__)
logger = LocalProxy(lambda: current_app.logger)


@core.before_request
def before_request_func():
    current_app.logger.name = 'core'


@core.route('/upload', methods=['POST'])
def upload():
    data = request.get_json()
    history = data["history"]
    # use jwt token for user authentication -> important. 
    # jwt token signed from ethereum address and valid for 45 minutes.  
    user_id = data["user_id"]
    for item in history:
        if not record_exists(item["id"], user_id):
            categorize_history.delay(item, user_id)
        else:
            logger.info('item exists id:', item["id"])
    return 'History Upload and Categorization is queued!'


@core.route('/', methods=['GET'])
@require_appkey
def restricted():
    return 'Congratulations! Your core-app restricted route is running via your API key!'
