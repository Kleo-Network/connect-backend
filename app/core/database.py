import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
from decimal import Decimal
import random 
from collections import defaultdict
import uuid
import tldextract
import datetime

aws_access_key = "AKIA3RWDXTFSIADMEAPE"
aws_secret_access_key = "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"
aws_region = "ap-south-1"

session = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)
dynamodb = session.resource('dynamodb')

def record_exists(id, user_id):
    table = dynamodb.Table('history')
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('id').eq(id)
    )
    return 'Items' in response and len(response['Items']) > 0

def create_user(user):
    table = dynamodb.Table('users')
    response = table.put_item(Item=user)
    return response

def upload_browsing_data(item,user_id):
    table = dynamodb.Table('history')
    item["user_id"] = user_id
    item["favourite"] = False
    item["id"] = str(random.randint(1, 10000000))
    
    extracted = tldextract.extract(item["url"])
    domain = "{}.{}".format(extracted.domain, extracted.suffix)
    item["icon"] = "https://www.google.com/s2/favicons?domain={}&sz=48".format(domain)
    
    item = json.loads(json.dumps(item), parse_float=Decimal)

    print("start")
    res = table.put_item(Item=item)
    print(item)
    print("uploaded")
    return True

def get_history(user_id, from_epoch, to_epoch, regex):
    table = dynamodb.Table('history')
    response = table.scan(
    FilterExpression="user_id = :user_id AND #lastVisitTime BETWEEN :start_date AND :end_date AND contains(#name_attr, :username)",
    ExpressionAttributeNames={
        "#lastVisitTime": "lastVisitTime",
        "#name_attr": "url"
    },
    ExpressionAttributeValues={
        ":user_id": user_id,
        ":username": regex,
        ":start_date": Decimal(from_epoch),
        ":end_date": Decimal(to_epoch)
        }
    )
    return response['Items']

def query_history(user_id, filters):
    table = dynamodb.Table('history')
    key_condition = Key('user_id').eq(user_id)
    conditions = []
    for attr, value in filters:
        condition = Attr(attr).eq(value)
        conditions.append(condition)
    
    filter_expression = conditions[0]
    for condition in conditions[1:]:
        filter_expression = filter_expression & condition
    
    response = table.query(
        KeyConditionExpression=key_condition,
        FilterExpression=filter_expression
    )
    return response['Items']

def delete_history_item(primary_id):
    table = dynamodb.Table('history')
    response = table.delete_item(Key={"item_id": primary_id })
    return response 

def add_to_favourites(item_id):
    table = dynamodb.Table('history')
    response = table.update_item(
        Key={
            'id': item_id
        },
        UpdateExpression="set isStarred = :d",
        ExpressionAttributeValues={
            ':d': True
        },
        ReturnValues="UPDATED_NEW"  # This will return the updated attributes. You can change this based on your needs.
    )
    return response
    

def get_favourites(user_id, domain_name):
    table = dynamodb.Table('history')
    response = table.scan(
    FilterExpression="user_id = :user_id AND contains(#url_params, :domain) AND isStarred = :fav",
    ExpressionAttributeNames={
        "#url_params": "url"
        },
    ExpressionAttributeValues={
        ":user_id": user_id,
        ":domain": domain_name,
        ":fav": True
        }
    )
    return response['Items']

def get_summary(user_id, domain_name):
    table = dynamodb.Table('history')
    response = table.scan(
    FilterExpression="user_id = :user_id AND contains(#url_params, :domain)",
    ExpressionAttributeNames={
        "#url_params": "url"
        },
    ExpressionAttributeValues={
        ":user_id": user_id,
        ":domain": domain_name
        }
    )
    return response['Items']

def get_time_batch(unix_timestamp):
    # Convert the timestamp to datetime object
    dt = datetime.datetime.fromtimestamp(unix_timestamp / 1000.0)  # divide by 1000 to convert ms to s
    hour = dt.hour

    # Determine the batch
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
def get_graph_query(user_id, fromEpoch, toEpoch):
    # Initial empty structure
    result = {
        "00-04": [],
        "04-08": [],
        "08-12": [],
        "12-16": [],
        "16-20": [],
        "20-24": []
        
    }
    table = dynamodb.Table('history')
    response = table.scan(
    FilterExpression="user_id = :user_id AND #visitTime BETWEEN :fromEpoch AND :toEpoch",
    ExpressionAttributeNames={
        "#visitTime": "visitTime",
    },
    ExpressionAttributeValues={
        ":user_id": user_id,
        ":fromEpoch": Decimal(fromEpoch),
        ":toEpoch": Decimal(toEpoch),
    })
    data = response['Items']
    print(data)
    # Iterate over each item in the database
    for item in data:
        batch = get_time_batch(float(item["lastVisitTime"]))
        category = item["category"].split(":")[1].strip()  # To get the actual category name
        category_group = item["category_group"]
        
        extracted = tldextract.extract(item["url"])
        domain = "{}.{}".format(extracted.domain, extracted.suffix)
        item["icon"] = "https://www.google.com/s2/favicons?domain={}&sz=48".format(domain)
        
        
        transformed_data = {
            "domain": domain,
            "name": item["title"],
            "visit": item["visitCount"],
            "icon": item["icon"],
            "subcategory": category,
            "Category Description": item["category_description"]
        }

        # Check if category exists in the batch
        category_exists = False
        for cat in result[batch]:
            if category_group in cat:
                cat[category_group].append(transformed_data)
                category_exists = True
                break

        # If category doesn't exist, create a new one
        if not category_exists:
            result[batch].append({category_group: [transformed_data]})

    return result


# def get_grpah_query(user_id, fromEpoch, toEpoch, divisions):
#     table = dynamodb.Table('history')
#     fromEpoch = Decimal(fromEpoch)
#     toEpoch = Decimal(toEpoch)
#     divisions = Decimal(divisions)
#     response = table.scan(
#     FilterExpression="user_id = :user_id AND #visitTime BETWEEN :fromEpoch AND :toEpoch",
#     ExpressionAttributeNames={
#         "#visitTime": "visitTime",
#     },
#     ExpressionAttributeValues={
#         ":user_id": user_id,
#         ":fromEpoch": fromEpoch,
#         ":toEpoch": toEpoch
#     }
# )
    
#     items = response['Items']
#     division_length = (toEpoch - fromEpoch) / divisions
#     results = defaultdict(dict)
#     for item in items:
#         division_index = int((int(item["visitTime"]) - fromEpoch) / division_length)
#         print(division_index)
#         category = item['category']
#         if category not in results[division_index]:
#             results[division_index][category] = []
#         results[division_index][category].append(item)
    
    
#     # hourly -> 24/4 => 00-04, 04-08,08-12,12-16,16-20,20-24  
#     # weekly -> monday, tuesday, wednesday, thursday, friday
#     # monthly -> week 1, week 2, week 3, week 4, week 5
#     # Last 6 months -> May, June, July, August, September, October 
#     {
#         "00-04": [
#             {"category_name 1":[
#                 {
#                 "domain": "domain url",
#                 "name": "title",
#                 "visit": "number of visits in this day/hour/week/month",
#                 "icon": "icon url",
#                 "subcategory": "Sub category",
#                 "Category Description": "Category Description"
#                 },
#                 {
#                 "domain": "domain url",
#                 "name": "title",
#                 "visit": "number of visits in this day/hour/week/month",
#                 "icon": "icon url",
#                 "subcategory": "Sub category",
#                 },
#                 "..."
#                 ]},
#             {"category_name 2":[
#                 {
#                 "domain": "domain url",
#                 "name": "title",
#                 "visit": "number of visits in this day/hour/week/month",
#                 "icon": "icon url",
#                 "subcategory": "Sub category",
#                 },"..."]
#                 },
#             ],
#         "04-08": same as 00-04
#         }    
    
#     return results

def get_entire_profile(user_id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('users')

    response = table.query(
        KeyConditionExpression="user_id = :user_id",
        ExpressionAttributeValues={
            ":user_id": user_id
        }
    )

    items = response['Items']
    return items[0] if items else None
def get_pinned_website(user_id):
    table = dynamodb.Table('pinned_websites')
    
    # Query the table for the given user_id
    response = table.scan(
    FilterExpression="user_id = :user_id",
    ExpressionAttributeValues={
        ":user_id": user_id
    })
    
    # Return the items from the response
    return response['Items']

def add_to_pinned_websites(user_id, domain_name, order, title):
    table = dynamodb.Table('pinned_websites')
    
    item = {
        'user_id': user_id,
        'domain_name': domain_name, # www.kleo.network
        'order': order,
        'name': title,
        'id':  str(uuid.uuid4()),
        'icon': "https://www.google.com/s2/favicons?domain={}&sz=48".format(domain_name)

    }
    
    response = table.put_item(Item=item)
    
    return response