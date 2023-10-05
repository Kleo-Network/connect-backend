from flask import Blueprint, current_app, request
from ..models.history import *
from werkzeug.local import LocalProxy

core = Blueprint('core', __name__)

logger = LocalProxy(lambda: current_app.logger)


@core.before_request
def before_request_func():
    current_app.logger.name = 'core'

# @core.route('/get_browsing_history_graph', methods=["GET"])
# def get_browsing_history_graph():
#     user_id = request.args.get('user_id')
#     from_epoch = request.args.get('from')
#     to_epoch = request.args.get('to')
#     response = get_graph_query(user_id, from_epoch, to_epoch)
#     return response

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
        if not record_exists(item["id"], user_id):
            print("upload will happen?")
            #categorize_history.delay(item, user_id)
        else:
            logger.info('item exists id:', item["id"])
    return 'History Upload and Categorization is queued!'

