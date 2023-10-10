from flask import Blueprint, current_app, request
from ..controllers.history import *
from werkzeug.local import LocalProxy
from ..controllers.graph import *
from ..celery.tasks import *
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

@core.route('/add_to_favourites', methods=['POST'])
def add_to_favourite():
    user_id = request.args.get('user_id')
    visitTime = request.args.get('visitTime')
    response = add_to_favourites(user_id, visitTime)
    return response

@core.route('/upload', methods=['POST'])
def upload():
    data = request.get_json()
    history = data["history"]
    # use jwt token for user authentication -> important. 
    # jwt token signed from ethereum address and valid for 45 minutes.  
    user_id = data["user_id"]
    chunks = [history[i:i + 25] for i in range(0, len(history), 25)]
    for index,chunk in enumerate(chunks):
        task = categorize_history.delay({"chunk": chunk, "user_id": user_id})
        
    return 'History Upload and Categorization is queued!'


from math import ceil

def batch_insert_items(table_name, items, custom_category):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    # Split the items into chunks of 25 (DynamoDB's BatchWriteItem limit)
    chunks = [items[i:i + 25] for i in range(0, len(items), 25)]
    
    for chunk in chunks:
        # Update category for each item in the chunk
        for item in chunk:
            item["category"] = custom_category

        request_items = {
            table_name: [
                {
                    'PutRequest': {
                        'Item': item
                    }
                }
                for item in chunk
            ]
        }

        response = dynamodb.batch_write_item(RequestItems=request_items)

        # If there are any unprocessed items, retry them
        while 'UnprocessedItems' in response and response['UnprocessedItems']:
            response = dynamodb.batch_write_item(RequestItems=response['UnprocessedItems'])
