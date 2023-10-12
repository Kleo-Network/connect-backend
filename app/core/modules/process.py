
import boto3
import datetime
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
import json
aws_access_key = "AKIA3RWDXTFSIADMEAPE"
aws_secret_access_key = "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"
aws_region = "ap-south-1"

session = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)
dynamodb = session.resource('dynamodb')

def upload_processed_data(user_id, from_epoch, to_epoch):
    graph_table = dynamodb.Table('graph_data')
    processed_data = process_data_day_wise(user_id, from_epoch, to_epoch)  # Assuming you have this function
    
    for item in processed_data:
        graph_table.put_item(Item=item)
        mark_as_processed(user_id, item["visitTime"])
    return True

def mark_as_processed(user_id, visitTime):
    """
    Update the item in DynamoDB and set processed = true.
    """
    table = dynamodb.Table('history')
    response = table.update_item(
        Key={
            'user_id': user_id,
            'visitTime': Decimal(str(visitTime))
        },
        UpdateExpression="set processed = :p",
        ExpressionAttributeValues={
            ':p': True
        },
        ReturnValues="UPDATED_NEW"
    )
    return response

def process_data_day_wise(user_id, from_epoch, to_epoch):
    results = {}

    table = dynamodb.Table('history')
    response = table.query(KeyConditionExpression=Key('user_id').eq("1") &
                            Key('visitTime').between(from_epoch, to_epoch))
    data = response['Items']
    print("lenght of original data")
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
    print("length of output data")
    print(len(sorted_output_data))
    json_dumps = json.dumps(sorted_output_data, indent=4,default=handle_decimal)
    print(json_dumps)
    return results

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

