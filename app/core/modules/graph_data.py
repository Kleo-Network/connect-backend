import boto3
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timedelta
import os
import time


# Initialize a session using Amazon DynamoDB credentials.
session = boto3.Session(
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    region_name=os.environ.get('AWS_DEFAULT_REGION')
)

dynamodb = session.resource('dynamodb')
table = dynamodb.Table('history')
graph_data_table = dynamodb.Table('graph_data')
users = dynamodb.Table('users')


def mark_as_unproccssed():
    response = users.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr('process_graph').eq(True)
    )
    items = response['Items']
    for item in items:
        users.update_item(Key={'id': item['id']},
                          UpdateExpresion='SET process_graph = :val', 
                          ExpressionAttributeValues={
                              ':val': False
                          },
                          ReturnValues='UPDATED_USER')
        
    return True

def get_user_unprocessed():
    response = users.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr('process_graph').eq(False)
    )
    if response['Items']:
        return response['Items'][0]  # Return the first unprocessed user
    else:
        return None
def update_user_processed(user_id, val):
    response = users.update_item(
        Key={
            'id': user_id,  # your primary key column name and value
        },
        UpdateExpression='SET process_graph = :val',
        ExpressionAttributeValues={
            ':val': val
        },
        ReturnValues="UPDATED_NEW"  # Returns all the attributes of the item post update
    )
    return response
def process_items(user_id, day_start=0, day_end = 90):
    # Define the time range (last 24 hours)
    if day_start != 0:
        now = datetime.now() - timedelta(days=day_start)
    else:
        now = datetime.now() 
    
    previous_timestamp = now - timedelta(days=day_end)
    # Timestamps in milliseconds
    start_timestamp = int(previous_timestamp.timestamp() * 1000)
    end_timestamp = int(now.timestamp() * 1000)

    # Pagination
    unprocessed_items = []
    last_evaluated_key = None

    while True:
        query_params = {
            'KeyConditionExpression': Key('user_id').eq(user_id) & 
                                      Key('visitTime').between(start_timestamp, end_timestamp)
        }

        if last_evaluated_key:
            query_params['ExclusiveStartKey'] = last_evaluated_key

        response = table.query(**query_params)
        
        unprocessed_items.extend(response['Items'])

        last_evaluated_key = response.get('LastEvaluatedKey')
        if not last_evaluated_key:
            break

    # Process and categorize each item, then mark as processed
    user_data = {}
    write_items = []
    print(len(unprocessed_items))
    for item in response['Items']:
    # Extracting needed information
        user_id = item['user_id']
        visit_epoch = float(item['visitTime'])
        visit_date = datetime.utcfromtimestamp(visit_epoch / 1000.0).strftime('%Y-%m-%d')  # date from epoch
        category = item['category']
        domain = item['domain']

    # Constructing structured data
        if user_id not in user_data:
            user_data[user_id] = {}

        if visit_date not in user_data[user_id]:
            user_data[user_id][visit_date] = []

        hour_bracket = get_hour_bracket(visit_epoch)

    # Search for an existing entry that matches the hour bracket, category, and domain
        existing_entry = None
        for entry in user_data[user_id][visit_date]:
            if entry['hour_bracket'] == hour_bracket and entry['Category'] == category and entry['domain'] == domain:
                existing_entry = entry
                break

        if existing_entry:
        # If found, we increment the 'visit_count' by 1
            existing_entry['visit_count'] += 1
        else:
        # If not, we create a new entry
            new_entry = {
            "hour_bracket": hour_bracket,
            "Category": category,
            "domain": domain,
            "visit_count": 1
        }
            user_data[user_id][visit_date].append(new_entry)
# Now `user_data` contains the structured data per user. You can further process it as needed, or save it to another DynamoDB table or a different kind of storage.

# To display the data or do other operations, you can iterate through `user_data`:
    for user_id, dates in user_data.items():
        for date, data in dates.items():
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            epoch_time = int(time.mktime(date_obj.timetuple()))
        # Prepare the data item for insertion
        # 'user_id' and 'date' are the primary keys of the 'graph_data' table
        # 'data' is the JSON-serialized version of the aggregated data
            item = {
            'user_id': user_id,
            'date': epoch_time,
            'data': data  # converting the data into a JSON string
            }

        # Insert the item into DynamoDB table
            write_items.append(item)
    return write_items
    # for user_id, dates in user_data.items():
    #     for date, data in dates.items():
    #         print(f"User ID: {user_id}, Date: {date}, Data: {json.dumps(data)}")
    
# Execute the process
def batch_insert_items(items):
    # Split the items into chunks of 25 (DynamoDB's BatchWriteItem limit)
    chunks = [items[i:i + 25] for i in range(0, len(items), 25)]
    
    for chunk in chunks:
        # Update category for each item in the chunk
        request_items = {
            'graph_data': [
                {
                    'PutRequest': {
                        'Item': item
                    }
                }
                for item in chunk
            ]
        }

        response = dynamodb.batch_write_item(RequestItems=request_items)
    return True
        # If there are any unprocessed items, retry them
        
def get_hour_bracket(epoch_time):
    hour = datetime.utcfromtimestamp(epoch_time / 1000.0).hour  # DynamoDB timestamp is in milliseconds
    if 0 <= hour < 4:
        return "00-04"
    elif 4 <= hour < 8:
        return "04-08"
    elif 8 <= hour < 12:
        return "08-12"
    elif 12 <= hour < 16:
        return "12-16"
    elif 16 <= hour < 20:
        return "16-20"
    else:
        return "20-24"

# Organizing the data
