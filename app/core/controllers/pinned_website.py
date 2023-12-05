import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
import json
import uuid
from datetime import datetime, timedelta
from ..models.aws_session import dynamodb
from ..celery.tasks import *


def get_pinned_graph_view(user_id, domain):
    user_domain_key = f"{user_id}#{domain}"
    graph_data_pinned_table = dynamodb.Table('pinned_graph_data')
    now = datetime.now()
    one_year_from_now = now - timedelta(days=900)
    start_date = int(one_year_from_now.timestamp())
    end_date = int(now.timestamp())

    try:
        response = graph_data_pinned_table.query(
            KeyConditionExpression=Key('domain_user_id').eq(user_domain_key) & 
                                    Key('date').between(Decimal(start_date), Decimal(end_date))
        )
        print(start_date)
        print(end_date)
        items = response.get('Items', [])
        return items
    except Exception as e:
        print(f"Error querying table: {e}")
        return []  


def get_domain_string(user_id, domain_string):
    table = dynamodb.Table('domains')
    response = table.scan(
    FilterExpression="contains(#dm, :val_domain)",
    ExpressionAttributeNames={"#dm": "domain"},
    ExpressionAttributeValues={':val_domain': domain_string}
    )
    print(response['Items'])
    for item in response['Items']:
        item["pinned"] = check_pinned_website(user_id, item["domain"])
        item["icon"] = "https://www.google.com/s2/favicons?domain={}&sz=48".format(item["domain"])
    return response['Items']


def get_pinned_website(user_id):
    table = dynamodb.Table('pinned_websites')
    response = table.scan(
        FilterExpression="user_id = :user_id",
        ExpressionAttributeValues={
            ":user_id": user_id
        }
    )
    for item in response['Items']:
        item["icon"] = "https://www.google.com/s2/favicons?domain={}&sz=48".format(item["domain"])
    return response['Items']

def remove_pinned_website_function(user_id,domain):
    table = dynamodb.Table('pinned_websites')
    response = table.delete_item(
            Key={
                'user_id': user_id,
                'domain': domain  # your primary key column name and value
            }
        )
    return response
def check_pinned_website(user_id, domain):
    table = dynamodb.Table('pinned_websites')
    response = table.get_item(Key={'user_id': user_id, 'domain': domain})
    if 'Item' in response:
        return True
    else:
        return False

def add_to_pinned_websites(user_id, domain_name, order, title):
    table = dynamodb.Table('pinned_websites')
    item = {
        'user_id': user_id,
        'domain': domain_name,
        'order': order,
        'title': title
    }
    response = table.put_item(Item=item)
    process_pinned_graph_data.delay(user_id, domain_name)
    return response
