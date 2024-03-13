import boto3
import time

from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timedelta
import os
from botocore.exceptions import ClientError
from decimal import Decimal
from collections import defaultdict
import pytz
from ..controllers.graph import *

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
processor = dynamodb.Table('processor')

def batch_insert_items(items):
    dynamodb = session.resource('dynamodb')
    chunks = [items[i:i + 25] for i in range(0, len(items), 25)]
    for chunk in chunks:
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

        try:
            response = dynamodb.batch_write_item(RequestItems=request_items)
            print("Batch write successful.")
            print(response)
            break  # Exit the loop if successful
        except ClientError as e:
            if e.response['Error']['Code'] == 'ProvisionedThroughputExceededException':
                print("Provisioned Throughput Exceeded, retrying...")
                attempt += 1
                time.sleep(2)  # Exponential backoff
            else:
                print(f"Error uploading chunk: {e}")
                return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False
    return True

def process_items_pinned_data(user_id, pinned_domain): 
    now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_timestamp = int((now - timedelta(days=180)).timestamp() * 1000)
    end_timestamp = int(now.timestamp() * 1000)

    table = dynamodb.Table('history')
    response = query_dynamodb(table, user_id, start_timestamp, end_timestamp, pinned_domain)
    
    items = response['Items']
    while 'LastEvaluatedKey' in response:
        response = query_dynamodb(table, user_id, start_timestamp, end_timestamp, pinned_domain, response['LastEvaluatedKey'])
        items.extend(response['Items'])

    output = defaultdict(lambda: defaultdict(lambda: {"data": defaultdict(int)}))

    for item in items:
        process_item(item, output)

    return store_and_format_output(output, pinned_domain)

def query_dynamodb(table, user_id, start_timestamp, end_timestamp, pinned_domain, last_key=None):
    try:
        query_params = {
            "KeyConditionExpression": Key('user_id').eq(user_id) & 
                                      Key('visitTime').between(Decimal(start_timestamp), Decimal(end_timestamp)),
            "FilterExpression": "contains(#url_attr, :domain_name)",
            "ExpressionAttributeNames": {"#url_attr": "url"},
            "ExpressionAttributeValues": {":domain_name": pinned_domain}
        }
        if last_key:
            query_params['ExclusiveStartKey'] = last_key
        return table.query(**query_params)
    except Exception as e:
        if "ProvisionedThroughputExceededException" in str(e):
            time.sleep(5)
            return query_dynamodb(table, user_id, start_timestamp, end_timestamp, pinned_domain, last_key)
        else:
            raise e

def process_item(item, output, timezone_str='Asia/Kolkata'):
    
    tz = pytz.timezone(timezone_str)
    date_date = datetime.fromtimestamp(float(item["visitTime"]) / 1000.0, tz)

    date_epoch = date_date.replace(hour=0, minute=0, second=0, microsecond=0)
    date_str = int(date_epoch.timestamp())
    time_bracket = get_hour_bracket(float(item["visitTime"]), timezone_str)

    user_id = item["user_id"]
    output[user_id][date_str]["data"][time_bracket] += 1

def store_and_format_output(output, pinned_domain):
    formatted_output = []
    graph_data_pinned_table = dynamodb.Table('pinned_graph_data')

    for user_id, dates in output.items():
        for date, data in dates.items():
            record = {
                "user_id": user_id,
                "date": date,
                "data": [{"time_bracket": tb, "visitCount": count} for tb, count in data["data"].items()]
            }
            formatted_output.append(record)
            store_record(graph_data_pinned_table, record, pinned_domain)

    return formatted_output

def store_record(table, record, pinned_domain):
    user_domain_key = f"{record['user_id']}#{pinned_domain}"
    data_json = json.dumps(record['data'])  # Convert data to JSON string
    item = {
        'domain_user_id': user_domain_key,
        'date': Decimal(record['date']),
        'domain': pinned_domain,
        'data': data_json
    }
    try:
        table.put_item(Item=item)
    except Exception as e:
        if "ProvisionedThroughputExceededException" in str(e):
            time.sleep(5)
            store_record(table, record, pinned_domain)
        else:
            raise e

def mark_history_processed(user_id, visitTime):
    table = dynamodb.Table('history')
    try:
        table.update_item(
                    Key={
                        'user_id': user_id,
                        'visitTime': Decimal(visitTime)
                    },
                    UpdateExpression='SET #proccessed = :val',
                    ExpressionAttributeNames={'#proccessed': 'proccessed'},
                    ExpressionAttributeValues={
                    ':val': True
                },
                ReturnValues="UPDATED_NEW")
    except: 
        time.sleep(4)
        table.update_item(
                    Key={
                        'user_id': user_id,
                        'visitTime': Decimal(visitTime)
                    },
                    UpdateExpression='SET #proccessed = :val',
                    ExpressionAttributeNames={'#proccessed': 'proccessed'},
                    ExpressionAttributeValues={
                    ':val': True
                },
                ReturnValues="UPDATED_NEW")
        
    return True

def update_counter_user_previous(user_id):
    response = users.update_item(
        Key={
            'id': user_id,  # your primary key column name and value
        },
        UpdateExpression='SET process_graph_previous_history = :val',
        ExpressionAttributeValues={
            ':val': True
        },
        ReturnValues="UPDATED_NEW"  # Returns all the attributes of the item post update
    )
    return True

def update_counter(user_id, counter):
    response = users.update_item(
        Key={
            'id': user_id,  # your primary key column name and value
        },
        UpdateExpression='SET process_graph_previous_history_counter = :val',
        ExpressionAttributeValues={
            ':val': counter
        },
        ReturnValues="UPDATED_NEW"  # Returns all the attributes of the item post update
    )
    return True

def mark_as_unproccssed(field_name):
    response = users.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr(field_name).eq(True)
    )
    items = response['Items']
    for item in items:
        users.update_item(Key={'id': item['id']},
                          UpdateExpression='SET #field_name = :val', 
                          ExpressionAttributeNames={'#field_name': field_name},
                          ExpressionAttributeValues={
                              ':val': False
                          },
                          ReturnValues='UPDATED_NEW')
        
    return True

def get_user_unprocessed_pinned_graph():
    response = users.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr('process_graph_pinned').eq(False)
    )
    if response['Items']:
        return response['Items'][0]  # Return the first unprocessed user
    else:
        return None

def get_user_unprocessed_graph_previous_history():
    response = users.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr('process_graph_previous_history').eq(False)
    )
    if response['Items']:
        return response['Items'][0]  # Return the first unprocessed user
    else:
        return None
    

def get_user_unprocessed_graph():
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

def get_process_graph_previous_history(user_id):
    try:
        response = users.get_item(
        Key={'id': user_id})
    
        if 'Item' in response:
            return response['Item']
        else:
            print(response)
    except:
        time.sleep(1)
        get_process_graph_previous_history(user_id)

def update_user_processed_previous_history(user_id, val):
    response = users.update_item(
        Key={
            'id': user_id,  # your primary key column name and value
        },
        UpdateExpression='SET process_graph_previous_history = :val',
        ExpressionAttributeValues={
            ':val': val
        },
        ReturnValues="UPDATED_NEW"  # Returns all the attributes of the item post update
    )
    return response


def scan_history_table(user_id, start_timestamp, end_timestamp):
    unprocessed_items = []
    last_evaluated_key = None

    while True:
        query_params = {
            'KeyConditionExpression': Key('user_id').eq(user_id) & 
                                Key('visitTime').between(start_timestamp, end_timestamp)
        }

        if last_evaluated_key:
            query_params['ExclusiveStartKey'] = last_evaluated_key

        try:
            response = table.query(**query_params)
        except Exception as e:
            print(f"Error scanning history table: {e}")
            time.sleep(4)
            continue

        unprocessed_items.extend(response['Items'])
        last_evaluated_key = response.get('LastEvaluatedKey')
        
        if not last_evaluated_key:
            break

    return unprocessed_items

def process_items(user_id, process_date):
    previous_timestamp = process_date - timedelta(days=1)
    start_timestamp = int(previous_timestamp.timestamp() * 1000)
    end_timestamp = int(process_date.timestamp() * 1000)

    unprocessed_items = scan_history_table(user_id, start_timestamp, end_timestamp)

    user_data = {}
    for item in unprocessed_items:
        process_item_data(item, user_data)

    write_items = prepare_write_items(user_data, user_id, process_date)
    write_to_dynamodb(write_items, user_id, process_date)

    return write_items

def process_item_data(item, user_data, timezone_str):
    user_id = item['user_id']
    visit_epoch = float(item['visitTime'])
    visit_date = datetime.utcfromtimestamp((visit_epoch / 1000.0), timezone_str).strftime('%Y-%m-%d')
    category = item['category']
    domain = item['domain']
    hour_bracket = get_hour_bracket(visit_epoch, timezone_str)

    user_data.setdefault(user_id, {}).setdefault(visit_date, [])

    existing_entry = next((entry for entry in user_data[user_id][visit_date] if entry['hour_bracket'] == hour_bracket and entry['Category'] == category and entry['domain'] == domain), None)

    if existing_entry:
        existing_entry['visit_count'] += 1
    else:
        user_data[user_id][visit_date].append({
            "hour_bracket": hour_bracket,
            "Category": category,
            "domain": domain,
            "visit_count": 1
        })

def prepare_write_items(user_data, user_id, process_date):
    write_items = []
    for dates in user_data.values():
        for data in dates.values():
            write_items.append({
                'user_id': user_id,
                'date': Decimal(process_date),
                'data': data,
                'last_update': Decimal(time.time())
            })
    return write_items

def write_to_dynamodb(write_items, user_id, process_date):
    with graph_data_table.batch_writer() as batch:
        for item in write_items:
            batch.put_item(Item=item)

    processor.put_item(
        Item={
            'user_id': user_id,
            'date': Decimal(process_date),
            'process_graph': True
        }
    )    
        
def get_hour_bracket(epoch_time, timezone_str="Asia/Kolkata"):
    utc_time = datetime.utcfromtimestamp(epoch_time / 1000.0)
    timezone = pytz.timezone(timezone_str)
    local_time = utc_time.astimezone(timezone)
    hour = local_time.hour
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
