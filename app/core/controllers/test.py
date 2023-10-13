import json
from datetime import datetime
import boto3
# Sample history data
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr

import math

aws_access_key = "AKIA3RWDXTFSIADMEAPE"
aws_secret_access_key = "cSwTtZp8ZwTMeNTCzMXvz0sYMcGn07FLSCpoOITI"
aws_region = "ap-south-1"

session = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)
dynamodb = session.resource('dynamodb')


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
delete_all_history_items()
  # Your list of dictionaries from the history table

# Initialize the output data structure

def handle_decimal(obj):
    """Converts Decimal objects to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(repr(obj) + " is not JSON serializable")

# Sample history data
def get_time_bracket(timestamp):
    hour = datetime.utcfromtimestamp(timestamp / 1000).hour
    if 0 <= hour < 4:
        return '00-04'
    elif 4 <= hour < 8:
        return '04-08'
    elif 8 <= hour < 12:
        return '08-12'
    elif 12 <= hour < 16:
        return '12-16'
    elif 16 <= hour < 20:
        return '16-20'
    else:
        return '20-24'
def get_result():
    results = {}

    table = dynamodb.Table('history')
    response = table.query(KeyConditionExpression=Key('user_id').eq("1"))
    data = response['Items']
    print(len(data))
    for item in data:
        date = datetime.utcfromtimestamp(int(item['visitTime']) / 1000).strftime('%Y-%m-%d')
        bracket = get_time_bracket(int(item['visitTime']))
        category = item['category']
        domain = item['domain']
        user_id = item['user_id']
        visit_count = item['visitCount']

        # Create unique key for results
        key = (user_id, date, bracket, category, domain)

        if key in results:
            results[key] += visit_count
        else:
            results[key] = visit_count

    # Transform results into desired output format
    output_data = []
    for (user_id, date, bracket, category, domain), category_visit_count in results.items():
        output_data.append({
            'user_id': user_id,
            'date': date,
            'bracket': bracket,
            'Category': category,
            'domain': domain,
            'domain_visit_count': category_visit_count
        })

    sorted_output_data = sorted(output_data, key=lambda x: x['date'])
    print(len(sorted_output_data))
    json_dumps = json.dumps(sorted_output_data, indent=4,default=handle_decimal)
    print(json_dumps)
    return results
get_result()
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

