import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
import json
import random
from collections import defaultdict
from ..modules.history import single_url_request
import time
from botocore.exceptions import ClientError
from flask import  jsonify

from ..models.aws_session import dynamodb


def scan_history_by_url_or_title(user_id, search_string, items_per_page=50, page = 1):

    table = dynamodb.Table('history')
    # Prepare the parameters for the scan operation
    params = {
        "KeyConditionExpression": Key('user_id').eq(user_id),
        "FilterExpression": "contains(#url, :val) OR contains(#title, :val)",
        "ExpressionAttributeNames": {
            "#url": "url",
            "#title": "title"
        },
        "ExpressionAttributeValues": {
            ':val': search_string
        },
        "ScanIndexForward": False  # Set to False for descending order
    }

    items = []
    count = 0
    final_count = int(page) * int(items_per_page)
    while True:
        response = table.query(**params)
        items.extend(response.get('Items', []))
        if 'LastEvaluatedKey' in response:
            params['ExclusiveStartKey'] = response['LastEvaluatedKey']
        else:
            break 
        
        if len(items) < int(items_per_page):
            break
        count = count  + len(response['Items'])
        if count > int(final_count):
            break
    
    # For example, to get a specific "page" of results:
    start_index = (int(page) - 1) * int(items_per_page)  # calculate based on your page number and items_per_page
    end_index = start_index + int(items_per_page)
    page_items = items[start_index:end_index]

    return page_items  # or return items for all the results without pagination


def domain_exists_or_insert(domain):
    table = dynamodb.Table("domains")
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('domain').eq(domain)
    )
    
    if response['Items']:
        return response['Items'][0]
    else:
        category_group, category_description, category = single_url_request(domain)
        item =  {'domain': domain,
                'category_group': category_group,
                'category_description': category_description, 
                'category': category}
        table.put_item(Item=item)
        return item
        

def record_exists(user_id, visitTime):
    table = dynamodb.Table('history')
    try:
        response = table.query(
       KeyConditionExpression=(
            Key('user_id').eq(str(user_id)) & 
            Key('visitTime').eq(Decimal(str(visitTime)))
        )
        )
        return 'Items' in response and len(response['Items']) > 0
    except:
        time.sleep(5)
        record_exists(user_id, visitTime)

def convert_floats_to_decimal(item):
    for key, value in item.items():
        if isinstance(value, float):
            item[key] = Decimal(str(value))
    return item

def upload_browsing_history_chunk(chunk):
    filtered_chunk = [convert_floats_to_decimal(item) for item in chunk if not record_exists(item['user_id'], item['visitTime'])]
    if not filtered_chunk:
        return False
    
    request_items = {
        'history': [
            {
                'PutRequest': {
                    'Item': item
                }
            }
            for item in filtered_chunk
            ]
        }
    try:
        response = dynamodb.batch_write_item(RequestItems=request_items)
        return True
    except boto3.exceptions.ProvisionedThroughputExceededException:
        print("Provisioned Throughput Exceeded, retrying in 30 seconds...")
        time.sleep(5)
        return upload_browsing_history_chunk(chunk)
    except Exception as e:
        print(f"Error uploading chunk: {e}")
        return False

def upload_browsing_data(item, user_id):
    try:
        table = dynamodb.Table('history')
        item["user_id"] = user_id
        item["favourite"] = False
        item["hidden"] = False
        item = json.loads(json.dumps(item), parse_float=Decimal)
        res = table.put_item(Item=item)
        return True
    except:
        time.sleep(5)
        pass
        

def get_history(user_id, from_epoch, to_epoch, regex):
    table = dynamodb.Table('history')
    response = table.query(
        KeyConditionExpression=Key('user_id').eq(user_id) & 
                            Key('visitTime').between(Decimal(from_epoch), Decimal(to_epoch)),
        FilterExpression="contains(#name_attr, :username)",
        ExpressionAttributeNames={
            "#name_attr": "url"
        },
        ExpressionAttributeValues={
            ":username": regex
        })
    return response['Items']

def fetch_history_item(user_id, visitTime):
    table = dynamodb.Table('history')
    response = table.get_item(
        Key={'user_id': user_id, 'visitTime': Decimal(visitTime)})
    return response['Item']


def delete_history_item(primary_id):
    table = dynamodb.Table('history')
    response = table.delete_item(Key={"item_id": primary_id })
    return response 

def add_to_favorites(user_id, visitTime):
    item = fetch_history_item(user_id,visitTime)
    table = dynamodb.Table('favourites')
    history_table = dynamodb.Table('history')
    
    try:
        response = history_table.update_item(
                    Key={
                        'user_id': user_id,
                        'visitTime': Decimal(visitTime)
                    },
                    UpdateExpression='SET #favourite = :val',
                    ExpressionAttributeNames={'#favourite': 'favourite'},
                    ExpressionAttributeValues={
                    ':val': True
                },
                ReturnValues="UPDATED_NEW")
        
        response = table.put_item(
           Item={
                'user_id': user_id,  # unique identifier for the favorite item
                'url': item["url"],  # identifier for the user
                'title': item["title"],
                'domain': item["domain"],
                'visitTime': item["visitTime"],
                'history_id': item["id"]
            }
        )
        return response
    except ClientError as e:
        print(f"Error adding item to favorites: {e}")
        return None

def hide_history_items_table(user_id, visit_times, hide=True):
    table = dynamodb.Table('history')
    try:
        for visit in visit_times:
            response = table.query(
            KeyConditionExpression=Key('user_id').eq(user_id) & 
                            Key('visitTime').eq(Decimal(visit)))
            response = table.update_item(
                    Key={
                        'user_id': user_id,
                        'visitTime': Decimal(visit)
                    },
                    UpdateExpression='SET #hidden = :val',
                    ExpressionAttributeNames={'#hidden': 'hidden'},
                    ExpressionAttributeValues={
                    ':val': hide
                },
                ReturnValues="UPDATED_NEW")
        return jsonify({'message': 'Executed Successfully'}), 200
    except ClientError as e:
        print(e)
        pass
        return jsonify({'error': str(e)}), 200
def remove_from_favorites(user_id, url):
    table = dynamodb.Table('favourites')

    try:
        response = table.delete_item(
            Key={
                'user_id': user_id,
                'url': url
            }
        )
        return response
    except ClientError as e:
        print(f"Error removing item from favorites: {e}")
        return None


def get_favourites(user_id, domain_name):
    fav_table = dynamodb.Table('favourites')
    response = fav_table.query(
    KeyConditionExpression=Key('user_id').eq(user_id),
    FilterExpression="contains(#url_params, :domain)",
    ExpressionAttributeNames={
            "#url_params": "domain"
        },
    ExpressionAttributeValues={
        ":domain": domain_name
    })
    return response['Items']

def get_summary(user_id, domain_name):
    table = dynamodb.Table('history')
    response = table.query(
        KeyConditionExpression=Key('user_id').eq(user_id),
        FilterExpression="contains(#url_params, :domain)",
        ExpressionAttributeNames={
            "#url_params": "url"
        },
        ExpressionAttributeValues={
            ":domain": domain_name
        },
        Select='COUNT')
    return response['Count']

def delete_history_items(user_id, visit_times):
    table = dynamodb.Table('history')
    for visit in visit_times:
        table.delete_item(
                Key={
                    'user_id': user_id,
                    'visitTime': Decimal(visit)   # Assuming domain is your sort key
                }
            )
    

def delete_history_regex(user_id, regex):
    table = dynamodb.Table('history')
    params = {
        "FilterExpression": "user_id = :user_id AND (contains(#url, :val) OR contains(#title, :val))",
        "ExpressionAttributeNames": {
            "#url": "url",
            "#title": "title"
        },
        "ExpressionAttributeValues": {
            ':val': regex,
            ':user_id': user_id
        }
    }
    response = table.scan(**params)
    for item in response['Items']:
        print(f"Deleting item with user_id: {item['user_id']} and domain: {item['domain']}")
        table.delete_item(
            Key={
                'user_id': item['user_id'],
                'visitTime': item['visitTime']   # Assuming domain is your sort key
            }
        )
    while 'LastEvaluatedKey' in response:
        response = table.scan(
            FilterExpression="category = :category_val",
            ExpressionAttributeValues={":category_val": cat},
            ExclusiveStartKey=response['LastEvaluatedKey']
        )

        for item in response['Items']:
            print(f"Deleting item with user_id: {item['user_id']} and domain: {item['domain']}")
            table.delete_item(
                Key={
                    'user_id': item['user_id'],
                    'visitTime': item['visitTime']   # Assuming domain is your sort key
                }
            )

def delete_category(user_id, cat):
    table = dynamodb.Table('history')
    response = table.scan(
        FilterExpression="user_id = :user_id AND category = :category_val",
        ExpressionAttributeValues={":category_val": cat, ":user_id": user_id}
    )

    # Loop through the items and delete each one
    for item in response['Items']:
        print(f"Deleting item with user_id: {item['user_id']} and domain: {item['domain']}")
        table.delete_item(
            Key={
                'user_id': item['user_id'],
                'visitTime': item['visitTime']   # Assuming domain is your sort key
            }
        )
        
    while 'LastEvaluatedKey' in response:
        response = table.scan(
           FilterExpression="user_id = :user_id AND category = :category_val",
            ExpressionAttributeValues={":category_val": cat, ":user_id": user_id},
            ExclusiveStartKey=response['LastEvaluatedKey']
        )

        for item in response['Items']:
            print(f"Deleting item with user_id: {item['user_id']} and domain: {item['domain']}")
            table.delete_item(
                Key={
                    'user_id': item['user_id'],
                    'visitTime': item['visitTime']   # Assuming domain is your sort key
                }
            )