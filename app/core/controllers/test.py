import json
from datetime import datetime
import boto3
# Sample history data
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr

import math

import boto3

# Initialize a session using Amazon DynamoDB credentials.
session = boto3.Session(
    aws_access_key_id="os.environ.get('AWS_ACCESS_KEY_ID')",
    aws_secret_access_key="os.environ.get('AWS_SECRET_ACCESS_KEY')",
    region_name="ap-south-1"
)

# Create DynamoDB resource.
dynamodb = session.resource('dynamodb')
# users_table = dynamodb.Table('users')

# user_ids = [
#     '4a29cd40-7981-4969-beea-c712ef80a0d0',
#     '5962973e-afc3-483f-a53c-fbecd49813f9',
#     'e09720d3-15cd-4b39-b9ca-e54534f3c31c',
#     '4c5fce3c-38aa-4199-b72e-73f195c8ab6d',
#     '05ecb209-8e92-4e2b-a2f0-c0d638f415ae',
#     '7ab8833b-8f22-487f-9d5a-9fa561ffedd9'
# ]

# # Use a batch writer to efficiently write multiple items to a DynamoDB table
# with users_table.batch_writer() as batch:
#     for user_id in user_ids:
#         batch.put_item(
#             Item={
#                 'id': user_id,
#                 'proccessed': False,
#                 'verified': True,
#                 'gitcoin_passport': False,
                 
#             }
#         )

# print("Batch write successful.")
# history_table = dynamodb.Table('history')  # change to your table's name

# # Placeholder for unique user IDs
# unique_user_ids = set()

# # Scan the history_table for unique user IDs
# response = None
# while response is None or 'LastEvaluatedKey' in response:
#     # If this is the first run, we don't have a LastEvaluatedKey yet
#     if response is None:
#         response = history_table.scan(
#             ProjectionExpression="user_id",  # Only retrieve the user_id field
#         )
#     else:
#         # Start the new scan where we left off
#         response = history_table.scan(
#             ProjectionExpression="user_id",
#             ExclusiveStartKey=response['LastEvaluatedKey']  # Continue scanning from the previous point
#         )

#     for item in response['Items']:
#         unique_user_ids.add(item['user_id'])

# # At this point, unique_user_ids set contains all unique user IDs

# # Now, if you want to scan the entire table, you can perform another scan without the ProjectionExpression.
# # This operation might be expensive in terms of read capacity units (RCUs) depending on the size of your table.

# # Placeholder for the full items
# all_items = []

# # Scan the history_table for all items
# response = None
# while response is None or 'LastEvaluatedKey' in response:
#     # If this is the first run, we don't have a LastEvaluatedKey yet
#     if response is None:
#         response = history_table.scan()
#     else:
#         # Start the new scan where we left off
#         response = history_table.scan(
#             ExclusiveStartKey=response['LastEvaluatedKey']  # Continue scanning from the previous point
#         )

#     all_items.extend(response['Items'])
#print(unique_user_ids)
def delete_category(cat):
    table = dynamodb.Table('history')
    response = table.scan(
    FilterExpression="category = :category_val",
    ExpressionAttributeValues={":category_val": cat}
    )
    print(response['Items'])

    # Loop through the items and delete each one
    for item in response['Items']:
        print(f"Deleting item with user_id: {item['user_id']} and domain: {item['domain']}")
        table.delete_item(
            Key={
                'user_id': item['user_id'],
                'visitTime': item['visitTime']   # Assuming domain is your sort key
            }
        )

    # Check for any remaining items (due to pagination in DynamoDB)
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

def delete_all_history_items():
    table = dynamodb.Table('history')
    
    # Scan the table to get all items.
    response = table.scan()
    items = response['Items']

    # Keep scanning until all items are fetched
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])

    # Delete each item
    for item in items:
        print("deleted")
        table.delete_item(Key={"user_id": item["user_id"], "visitTime": item["visitTime"]})

    print(f"Deleted {len(items)} items from the history table.")

# Call the function to delete all items
#delete_category("Pornography")
#delete_category("Search Engines and Portals")
  # Your list of dictionaries from the history table

# Initialize the output data structure


# Sample history data

def get_domain(url):
    return url.split("//")[-1].split("/")[0].split("?")[0]

# Grouping by hours of the day
def group_by_hour(timestamp):
    dt_object = datetime.utcfromtimestamp(timestamp/1000)  # Convert to seconds
    hour = dt_object.hour
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
    elif 20 <= hour < 24:
        return "20-24"

# Grouping by days of the week
def group_by_day(timestamp):
    dt_object = datetime.utcfromtimestamp(timestamp/1000)
    return dt_object.strftime('%A')

# Grouping by weeks of the month
def group_by_week(timestamp):
    dt_object = datetime.utcfromtimestamp(timestamp/1000)
    day_of_month = dt_object.day
    week_of_month = math.ceil(day_of_month / 7.0)
    return f"Week {week_of_month}"

grouping_methods = {
    'hour': group_by_hour,
    'day': group_by_day,
    'week': group_by_week
}

def process_data(group_by, history_data):
    # Choose the grouping method based on the parameter
    group_function = grouping_methods[group_by]

    # Empty output data
    output_data = {}

    for entry in history_data:
        group_value = group_function(int(entry["lastVisitTime"]))
        category = entry["category"]
        domain = get_domain(entry["url"])

        if group_value not in output_data:
            output_data[group_value] = {}

        if category not in output_data[group_value]:
            output_data[group_value][category] = {
                "domains": {},
                "totalCategoryVisits": 0
            }
        
        if domain not in output_data[group_value][category]["domains"]:
            output_data[group_value][category]["domains"][domain] = 0
        
        output_data[group_value][category]["domains"][domain] += 1
        output_data[group_value][category]["totalCategoryVisits"] += 1

    # Convert domain data to desired output format
    for group_value, categories in output_data.items():
        for category, data in categories.items():
            domains_list = [{"domain": k, "visitCounterTimeRange": v} for k, v in data["domains"].items()]
            output_data[group_value][category]["domains"] = domains_list

    return output_data

# To use:
def graph_query(group_by_parameter):
    table = dynamodb.Table('history')
    response = table.scan()
    history_data = response['Items']
    result = process_data(group_by_parameter, history_data)
    return result

def update_history_items_by_user_id(user_id):
    table = dynamodb.Table('history')
    
    # Scan the table to get all items for the given user_id.
    response = table.scan(
        FilterExpression=Attr('user_id').eq(user_id)
    )
    items = response['Items']

    # Keep scanning until all items are fetched
    while 'LastEvaluatedKey' in response:
        response = table.scan(
            FilterExpression=Attr('user_id').eq(user_id),
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        items.extend(response['Items'])

    # Update each item
    for item in items:
        print("update item with id: {}".format(item["id"]))
        # Here you can modify the item as needed, e.g.:
        # item['new_attribute'] = 'new_value'
        
        # Call the update_item method to update the item in DynamoDB
        table.update_item(
            Key={
                "user_id": item["user_id"],
                "visitTime": item["visitTime"]  # Assuming 'visitTime' is the sort key
            },
            UpdateExpression="SET user_id = :val",  # Specify your update expression
            ExpressionAttributeValues={
                ":val": "0x86B06319b906e61631f7edbe5A3fe2Edb95A3faE"  # Provide the new value
            }
        )
        print(f"Updated item with user_id: {item['user_id']} and visitTime: {item['visitTime']}")

    print(f"Updated {len(items)} items in the history table for user_id: {user_id}.")

# Call the function to update items for a specific user_id
update_history_items_by_user_id('e09720d3-15cd-4b39-b9ca-e54534f3c31c')
