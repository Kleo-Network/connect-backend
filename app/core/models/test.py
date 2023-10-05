import json
from datetime import datetime
import boto3
# Sample history data
from decimal import Decimal

aws_access_key = "os.environ.get('AWS_ACCESS_KEY_ID')"
aws_secret_access_key = "os.environ.get('AWS_SECRET_ACCESS_KEY')"
aws_region = "ap-south-1"

session = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)
dynamodb = session.resource('dynamodb')

table = dynamodb.Table('history')

response = table.scan()

history_data = response['Items']  # Your list of dictionaries from the history table

# Initialize the output data structure
output_data = {
    "00-04": {},
    "04-08": {},
    "08-12": {},
    "12-16": {},
    "16-20": {},
    "20-24": {}
}

def get_time_range(timestamp):
    print(timestamp)
    timestamp = int(timestamp)
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

def get_domain(url):
    # Extract domain name from URL
    return url.split("//")[-1].split("/")[0].split("?")[0]

for entry in history_data:
    time_range = get_time_range(entry["lastVisitTime"])
    category = entry["category"]
    domain = get_domain(entry["url"])

    # Update category and domain data
    if category not in output_data[time_range]:
        output_data[time_range][category] = {
            "domains": {},
            "totalCategoryVisits": 0
        }
    
    if domain not in output_data[time_range][category]["domains"]:
        output_data[time_range][category]["domains"][domain] = 0
    
    output_data[time_range][category]["domains"][domain] += 1
    output_data[time_range][category]["totalCategoryVisits"] += 1

# Convert domain data to desired output format
for time_range, categories in output_data.items():
    for category, data in categories.items():
        domains_list = [{"domain": k, "visitCounterTimeRange": v} for k, v in data["domains"].items()]
        output_data[time_range][category]["domains"] = domains_list

print(json.dumps(output_data, indent=4))
