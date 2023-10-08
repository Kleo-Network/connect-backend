from flask import Blueprint, current_app, request
from ..models.history import *
from ..models.pinned_website import *
from ..models.graph import *
from werkzeug.local import LocalProxy

core = Blueprint('core', __name__)

logger = LocalProxy(lambda: current_app.logger)
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
    title = data["title"]
    response = add_to_pinned_websites(user_id, domain, order, title)
    return response

@core.route('/get_pinned_data_domain', methods=['GET'])
def get_pinned_data_domain():
    user_id = request.args.get('user_id')
    from_epoch = request.args.get('from')
    to_epoch = request.args.get('to')
    domain_name = request.args.get('domain_name')
    filter = request.args.get('filter')
    response = graph_query(filter, user_id, from_epoch, to_epoch, domain_name)
    return response


@core.route('/get_pinned_summary_domain', methods=['GET'])
def get_pinned_summary_domain():
    user_id = request.args.get('user_id')
    domain_name = request.args.get('domain_name')
    summary = get_summary(user_id, domain_name)
    fav = get_favourites(user_id, domain_name)
    return {"total_visit_count": len(summary), "favourites": fav}  