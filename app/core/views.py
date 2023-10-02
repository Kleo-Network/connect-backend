
from flask import Blueprint, current_app, request
from werkzeug.local import LocalProxy

from authentication import require_appkey
#from  .database import record_exists
from .tasks import categorize_history
from .history import single_url_request
from .database import *

core = Blueprint('core', __name__)
logger = LocalProxy(lambda: current_app.logger)


@core.before_request
def before_request_func():
    current_app.logger.name = 'core'

@core.route('/get_browsing_history_by_category', methods=["GET"])
def get_browsing_history_by_category():
    filters = request.args.get('filters')
    

@core.route('/get_pinned_websites', methods=["GET"])
def get_pinned_websites_for_user():
    # Initialize the DynamoDB resource and the table
    user_id = request.args.get('user_id')
    pinned_Websites = get_pinned_website(user_id)
    return pinned_Websites
    

@core.route('/add_pinned_website', methods=['POST'])
def add_pinned_website():
    data = request.get_json()
    user_id = data["user_id"]
    domain = data["domain"]
    order = data["order"]
    response = add_to_pinned_websites(user_id, domain, order)
    return response

@core.route('/get_pinned_data_domain', methods=['GET'])
def get_pinned_data_domain():
    user_id = request.args.get('user_id')
    from_epoch = request.args.get('from')
    to_epoch = request.args.get('to')
    domain_name = request.args.get('domain_name')
    return get_history(user_id, from_epoch, to_epoch, domain_name)


@core.route('/get_pinned_summary_domain', methods=['GET'])
def get_pinned_summary_domain():
    user_id = request.args.get('user_id')
    domain_name = request.args.get('domain_name')
    summary = get_summary(user_id, domain_name)
    fav = get_favourites(user_id, domain_name)
    total_visit_count = 0
    for item in summary:
        total_visit_count += int(item["visitCount"])
    return {"total_visit_count": total_visit_count, "favourites": fav}    

@core.route('/add_to_favourites', methods=['POST'])
def add_to_favourite():
    item_id = request.args.get('item_id')
    response = add_to_favourites(item_id)
    return response

@core.route('/upload', methods=['POST'])
def upload():
    data = request.get_json()
    history = data["history"]
    # use jwt token for user authentication -> important. 
    # jwt token signed from ethereum address and valid for 45 minutes.  
    user_id = data["user_id"]
    for index,item in enumerate(history):
        #if not record_exists(item["id"], user_id):
        #item = single_url_request(item["url"], item)
        categorize_history.delay(item, user_id)
        #upload_browsing_data(item, user_id)
        #else:
        #    logger.info('item exists id:', item["id"])
    return 'History Upload and Categorization is queued!'


@core.route('/', methods=['GET'])
@require_appkey
def restricted():
    return 'Congratulations! Your core-app restricted route is running via your API key!'
