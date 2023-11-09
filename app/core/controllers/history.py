import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
import json
import random
from collections import defaultdict
from ..modules.history import single_url_request
import time

from ..models.aws_session import dynamodb


def scan_history_by_url_or_title(user_id, search_string, page=1, items_per_page=10):
    table = dynamodb.Table('history')

    # Calculate the number of scans needed to reach the desired page
    scans_needed = int(page)

    # Initial params
    params = {
        "FilterExpression": "user_id = :user_id AND (contains(#url, :val) OR contains(#title, :val))",
        "ExpressionAttributeNames": {
            "#url": "url",
            "#title": "title"
        },
        "ExpressionAttributeValues": {
            ':val': search_string,
            ':user_id': user_id
        },
        "Limit": int(items_per_page)
    }

    while scans_needed > 0:
        # If this isn't the first scan, set the ExclusiveStartKey to the last key from the previous scan
        if 'LastEvaluatedKey' in params:
            params['ExclusiveStartKey'] = params['LastEvaluatedKey']

        response = table.scan(**params)

        # If there's no LastEvaluatedKey in the response, then there's no more data to read
        if 'LastEvaluatedKey' not in response:
            if scans_needed > 1:
                # If we still haven't reached our desired page and there's no more data, return an empty list
                return []
            break
        else:
            # If there is a LastEvaluatedKey, we reduce our scans_needed counter and set the next ExclusiveStartKey
            params['LastEvaluatedKey'] = response['LastEvaluatedKey']
            scans_needed -= 1

    return response['Items']

def domain_exists_or_insert(domain):
    table = dynamodb.Table("domains")
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('domain').eq(domain)
    )
    
    if response['Items']:
        print(response['Items'])
        return response['Items'][0]
    else:
        category_group, category_description, category = single_url_request(domain)
        # Insert domain into the table
        item =  {'domain': domain,
                'category_group': category_group,
                'category_description': category_description, 
                'category': category}
        table.put_item(Item=item)
        return item
        

def record_exists(user_id, visitTime):
    table = dynamodb.Table('history')
    response = table.query(
       KeyConditionExpression=(
            Key('user_id').eq(str(user_id)) & 
            Key('visitTime').eq(Decimal(str(visitTime)))
        )
    )
    return 'Items' in response and len(response['Items']) > 0

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
    except dynamodb.exceptions.ProvisionedThroughputExceededException:
        print("Provisioned Throughput Exceeded, retrying in 30 seconds...")
        time.sleep(10)
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

def delete_history_item(primary_id):
    table = dynamodb.Table('history')
    response = table.delete_item(Key={"item_id": primary_id })
    return response 

def add_to_favourites(user_id, visitTime):
    table = dynamodb.Table('history')
    
    response = table.update_item(
        Key={
            'user_id': user_id,
            'visitTime': Decimal(visitTime)  # Assuming visitTime is a number (epoch time)
        },
        UpdateExpression="set favourite = :d",
        ExpressionAttributeValues={
            ':d': True
        },
        ReturnValues="UPDATED_NEW"
    )

    return response

def get_favourites(user_id, domain_name):
    table1 = dynamodb.Table('history')
    response = table1.query(
    KeyConditionExpression=Key('user_id').eq(user_id),
    FilterExpression="contains(#url_params, :domain) AND favourite = :is_starred",
    ExpressionAttributeNames={
            "#url_params": "url"
        },
    ExpressionAttributeValues={
        ":is_starred": True,
        ":domain": domain_name
    },
    ConsistentRead=True
)
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

