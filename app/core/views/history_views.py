from flask import Blueprint, current_app, request
from ..controllers.history import *
from werkzeug.local import LocalProxy
from ..controllers.graph import *
from ..celery.tasks import *
from math import ceil
from celery import chord
core = Blueprint('core', __name__)

logger = LocalProxy(lambda: current_app.logger)


@core.before_request
def before_request_func():
    current_app.logger.name = 'core'

@core.route('/get_browsing_history_graph', methods=["GET"])
def get_browsing_history_graph():
    user_id = request.args.get('user_id')
    from_epoch = request.args.get('from')
    to_epoch = request.args.get('to')
    filter = request.args.get('filter')
    response = graph_query(filter, user_id, from_epoch, to_epoch)
    return response

@core.route('/get_favourites_domain', methods=['GET'])
def get_favourites_domain():
    user_id = request.args.get('user_id')
    resposne = get_favourites_domain(user_id)

@core.route('/hide_history_items', methods=['POST'])
def hide_history_items():
    data=request.get_json()
    user_id = data['user_id']
    visitTimes = data["visit_times"]
    hide = data["hide"]
    response = hide_history_items_table(user_id, visitTimes, hide)
    return response

@core.route('/add_to_favourites', methods=['POST'])
def add_to_favourite():
    user_id = request.args.get('user_id')
    visitTime = request.args.get('visitTime')
    response = add_to_favorites(user_id, visitTime)
    return response
@core.route('/remove_from_favourites', methods=['POST'])
def remove_from_favourites():
    user_id = request.args.get('user_id')
    url = request.args.get('url')
    response = remove_from_favorites(user_id,url)
    return response

@core.route('/scan_history_by_url_or_title', methods=['GET'])
def search():
    search = request.args.get('search')
    user_id = request.args.get('user_id')
    page = request.args.get('page')
    size = request.args.get('size')
    response = scan_history_by_url_or_title(user_id, search, size,page)
    return response

@core.route('/delete_history_items', methods=['DELETE'])
def delete_history_items():
    data = request.get_json()
    user_id = data["user_id"]
    # you need to make this on the basis of celery task!
    if 'category' in data:
        delete_category(user_id, data['category'])
    elif 'regex' in data:
        delete_history_regex(user_id, data['regex'])
    elif 'visit_times' in data:
        delete_history_items(user_id, data['visit_times'])
    return jsonify({"message": "Deleted Items successfulyy"})
    
@core.route('/upload', methods=['POST'])
def upload():
    data = request.get_json()
    history = data["history"]
    user_id = data["user_id"]
    if "signup" in data:
        signup = data["signup"]
    else:
        signup = False
    
    chunks = [history[i:i + 25] for i in range(0, len(history), 25)]
    tasks = [categorize_history.s({"chunk": chunk, "user_id": user_id}) for chunk in chunks]
    params = {"user_id": user_id, "signup": signup}
    callback = process_graph_data.s(params)
    chord(tasks)(callback)
        
    return 'History Upload and Categorization is queued!'



