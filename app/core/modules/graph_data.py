import boto3
import time

from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timedelta
import os
from botocore.exceptions import ClientError
from decimal import Decimal
from collections import defaultdict

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
        print("chunk")
        print(request_items)

        try:
            response = dynamodb.batch_write_item(RequestItems=request_items)
            print("Batch write successful.")
            print(response)
            break  # Exit the loop if successful
        except ClientError as e:
            if e.response['Error']['Code'] == 'ProvisionedThroughputExceededException':
                print("Provisioned Throughput Exceeded, retrying...")
                attempt += 1
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"Error uploading chunk: {e}")
                return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False
    return True

def process_items_pinned_data(user_id, pinned_domain, day_start=0):
    if day_start != 0:
        now = (datetime.now()).date() - timedelta(days=day_start)
    else:
        now = datetime.now()
    
    now = datetime.combine(now, datetime.min.time())
    date=now.timestamp()
    previous_timestamp = now - timedelta(days=1)
    print("#1")
    start_timestamp = int(previous_timestamp.timestamp() * 1000)
    end_timestamp = int(now.timestamp() * 1000)
    table = dynamodb.Table('history')
    response = table.query(
                            KeyConditionExpression=Key('user_id').eq(user_id) & 
                            Key('visitTime').between(Decimal(start_timestamp), Decimal(end_timestamp)),
                            FilterExpression="contains(#url_attr, :domain_name)",
                            ExpressionAttributeNames={
                                "#url_attr": "url"
                            },
                            ExpressionAttributeValues={
                                ":domain_name": pinned_domain
                            })
    items = response['Items']
    print("#2")
    while 'LastEvaluatedKey' in response:
        response = table.query(
                            KeyConditionExpression=Key('user_id').eq(user_id) & 
                            Key('visitTime').between(Decimal(start_timestamp), Decimal(end_timestamp)),
                            FilterExpression="contains(#url_attr, :domain_name)",
                            ExpressionAttributeNames={
                                "#url_attr": "url"
                            },
                            ExpressionAttributeValues={
                                ":domain_name": pinned_domain
                            },
                            ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])
            
    
    print("#3")
    print(items)
    output = defaultdict(lambda: defaultdict(lambda: {"data": defaultdict(int)}))

    for item in items:
        date_date = datetime.fromtimestamp(float(item["visitTime"]) / 1000.0)
        date_epoch = date_date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_str = int(date_epoch.timestamp())
        time_bracket = get_hour_bracket(float(item["visitTime"]))

        user_id = item["user_id"]
        output[user_id][date_str]["data"][time_bracket] += 1

    # Convert the output to the desired format
    formatted_output = []
    for user_id, dates in output.items():
        for date, data in dates.items():
            formatted_output.append({
                "user_id": user_id,
                "date": date,
                "data": [{"time_bracket": tb, "visitCount": count} for tb, count in data["data"].items()]
            })
    
    graph_data_pinned_table = dynamodb.Table('pinned_graph_data')
    for record in formatted_output:
        user_domain_key = f"{record['user_id']}#{pinned_domain}"
        data_json = json.dumps(record['data'])  # Convert the data to a JSON string

        # Construct the item to insert
        item = {
            'domain_user_id': user_domain_key,
            'date': Decimal(record['date']),
            'domain': pinned_domain,
            'data': data_json
        }

        graph_data_pinned_table.put_item(Item=item)
    return formatted_output

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

def process_items(user_id, day_start=0):
   
    history_table = dynamodb.Table('history')
    if day_start != 0:
        now = (datetime.now()).date() - timedelta(days=day_start)
    else:
        now = datetime.now()
    
    now = datetime.combine(now, datetime.min.time())
    date=now.timestamp()
    previous_timestamp = now - timedelta(days=1)
    # Timestamps in milliseconds
    start_timestamp = int(previous_timestamp.timestamp() * 1000)
    end_timestamp = int(now.timestamp() * 1000)
    print(start_timestamp)
    print(end_timestamp)
    unprocessed_items = []
    last_evaluated_key = None
    while True:
        scan_params = {
        'FilterExpression': Key('user_id').eq(user_id) & 
                            Key('visitTime').between(start_timestamp, end_timestamp)
        }
        if last_evaluated_key is not None:
            scan_params['ExclusiveStartKey'] = last_evaluated_key
        try:
            response = history_table.scan(**scan_params)
        except:
            time.sleep(4)
            response = history_table.scan(**scan_params)

        unprocessed_items.extend(response['Items'])
        last_evaluated_key = response.get('LastEvaluatedKey')
        print(last_evaluated_key)
        if not last_evaluated_key:
            break

    user_data = {}
    write_items = []
    count  = 0
    for item in unprocessed_items:
        user_id = item['user_id']
        visit_epoch = float(item['visitTime'])
        visit_date = datetime.utcfromtimestamp(visit_epoch / 1000.0).strftime('%Y-%m-%d')  # date from epoch
        category = item['category']
        domain = item['domain']
        
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
            existing_entry['visit_count'] += 1
        else:
            new_entry = {
                "hour_bracket": hour_bracket,
                "Category": category,
                "domain": domain,
                "visit_count": 1
            }
            user_data[user_id][visit_date].append(new_entry)
    
    for d_, dates in user_data.items():
        for d, data in dates.items():
            item = {
            'user_id': user_id,
            'date': Decimal(date),
            'data': data ,
            'last_update': time.time()
            }
            write_items.append(item)
    
    for item in write_items:
        response = graph_data_table.put_item(Item=item)
    response = processor.put_item(
        Item={
            'user_id': user_id,
            'date': Decimal(date),
            'process_graph': True
        }
    )
    return write_items
    # for user_id, dates in user_data.items():
    #     for date, data in dates.items():
    #         print(f"User ID: {user_id}, Date: {date}, Data: {json.dumps(data)}")
    
        
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
print(datetime.now())