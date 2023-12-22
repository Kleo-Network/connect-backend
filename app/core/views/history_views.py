from flask import Blueprint, current_app, request
from ..controllers.history import *
from werkzeug.local import LocalProxy
from ..controllers.graph import *
from ..celery.tasks import *
from math import ceil
from celery import chord
from .auth_views import token_required
from ..controllers.checks import *
core = Blueprint('core', __name__)

logger = LocalProxy(lambda: current_app.logger)


@core.before_request
def before_request_func():
    current_app.logger.name = 'core'

@core.route('/get_browsing_history_graph', methods=["GET"])
@token_required
def get_browsing_history_graph(**kwargs):
    user_id = request.args.get('user_id')
    from_epoch = request.args.get('from')
    to_epoch = request.args.get('to')
    filter = request.args.get('filter')
    user = get_process_graph_previous_history(user_id)
    if filter == "day" and user["process_graph"] == "False":
        response = {"processing": True}
        return response 
    if filter == "month" and user["process_graph_previous_history"] == False:
        response = {"prcessing": True}
        return response        
    response = graph_query(filter, user_id, from_epoch, to_epoch)
    if 'items' in response:
        response['items'] = [item for item in response['items'] if item.get("Category") != "Pornography"]
    return response

@core.route('/get_favourites_domain', methods=['GET'])
@token_required
def get_favourites_domain(**kwargs):
    user_id = request.args.get('user_id')
    resposne = get_favourites_domain(user_id)

@core.route('/hide_history_items', methods=['POST'])
@token_required
def hide_history_items(**kwargs):
    data=request.get_json()
    user_id = data['user_id']
    visitTimes = data["visit_times"]
    hide = data["hide"]
    if user_id != kwargs.get('user_data')['payload']['publicAddress']:
        return "does not match!",501
    response = hide_history_items_table(user_id, visitTimes, hide)
    return response

@core.route('/add_to_favourites', methods=['POST'])
@token_required
def add_to_favourite(**kwargs):
    user_id = request.args.get('user_id')
    visitTime = request.args.get('visitTime')
    if user_id != kwargs.get('user_data')['payload']['publicAddress']:
        return "does not match!", 501
    response = add_to_favorites(user_id, visitTime)
    return response
@core.route('/remove_from_favourites', methods=['POST'])
@token_required
def remove_from_favourites(**kwargs):
    user_id = request.args.get('user_id')
    url = request.args.get('url')
    if user_id != kwargs.get('user_data')['payload']['publicAddress']:
        return "does not match!", 501
    response = remove_from_favorites(user_id,url)
    return response

@core.route('/scan_history_by_url_or_title', methods=['GET'])
@token_required
def search(**kwargs):
    search = request.args.get('search')
    user_id = request.args.get('user_id')
    page = request.args.get('page')
    size = request.args.get('size')
    print(user_id)
    print(kwargs.get('user_data'))
    if user_id != kwargs.get('user_data')['payload']['publicAddress']:
        return "does not match!", 501
    response = scan_history_by_url_or_title(user_id, search, size,page)
    return response

@core.route('/delete_history_items', methods=['DELETE'])
@token_required
def delete_history_items_api(**kwargs):
    data = request.get_json()
    user_id = data["user_id"]
    if user_id != kwargs.get('user_data')['payload']['publicAddress']:
        return "does not match!", 501
    # you need to make this on the basis of celery task!
    if 'category' in data:
        delete_category(user_id, data['category'])
    elif 'regex' in data:
        delete_history_regex(user_id, data['regex'])
    elif 'visit_times' in data:
        delete_history_items(user_id, data['visit_times'])
    return jsonify({"message": "Deleted Items successfulyy"})
    
@core.route('/upload', methods=['POST'])
@token_required
def upload(**kwargs):
    data = request.get_json()
    history = data["history"]
    user_id = data["user_id"]
    
    chunks = [history[i:i + 25] for i in range(0, len(history), 25)]
    tasks = [categorize_history.s({"chunk": chunk, "user_id": user_id}) for chunk in chunks]
    
    callback = upload_history_next_two_days.s(user_id)
    chord(tasks)(callback)
    return 'History Upload and Categorization is queued!'

@core.route('/process_items', methods=['POST'])
def process_items_post_upload():
    data = request.get_json()
    user_id = data["user_id"]
    signup = data["signup"]
    counter = data["days"]
    check_user_graphs = check_user_graphs_fn(user_id, counter)
    if check_user_graphs:
        return "Items are Processed!"
    else:
        params = {"user_id": user_id, "signup": signup, "counter": counter}
        process_graph_data.delay(params)
        return "Processing Items!"

