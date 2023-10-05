import json
from datetime import datetime
import boto3
import math
from decimal import Decimal

aws_access_key = "AKIA3RWDXTFSIADMEAPE"
aws_secret_access_key = "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"
aws_region = "ap-south-1"

session = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)
dynamodb = session.resource('dynamodb')

def get_domain(url):
    return url.split("//")[-1].split("/")[0].split("?")[0]

def group_by_hour(timestamp):
    dt_object = datetime.utcfromtimestamp(timestamp/1000)
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

def group_by_day(timestamp):
    dt_object = datetime.utcfromtimestamp(timestamp/1000)
    return dt_object.strftime('%A')

def group_by_week(timestamp):
    dt_object = datetime.utcfromtimestamp(timestamp/1000)
    day_of_month = dt_object.day
    week_of_month = math.ceil(day_of_month / 7.0)
    return f"Week {week_of_month}"

def group_by_month(timestamp):
    dt_object = datetime.utcfromtimestamp(timestamp/1000)
    return dt_object.strftime('%B')

grouping_methods = {
    'hour': group_by_hour,
    'day': group_by_day,
    'week': group_by_week,
    'month': group_by_month
}

def initialize_output_for_hours():
    return {
        "00-04": {},
        "04-08": {},
        "08-12": {},
        "12-16": {},
        "16-20": {},
        "20-24": {}
    }

def initialize_output_for_days():
    return {
        "Monday": {},
        "Tuesday": {},
        "Wednesday": {},
        "Thursday": {},
        "Friday": {},
        "Saturday": {},
        "Sunday": {}
    }

def initialize_output_for_weeks():
    return {
        "Week 1": {},
        "Week 2": {},
        "Week 3": {},
        "Week 4": {},
        "Week 5": {}
    }

def initialize_output_for_year():
    return {
        "January": {},
        "February": {},
        "March": {},
        "April": {},
        "May": {},
        "June": {},
        "July": {},
        "August": {},
        "September": {},
        "October": {},
        "November": {},
        "December": {}
    }

initialization_methods = {
    'hour': initialize_output_for_hours,
    'day': initialize_output_for_days,
    'week': initialize_output_for_weeks,
    'month': initialize_output_for_year
}

def process_data(group_by, history_data):
    group_function = grouping_methods[group_by]
    output_data = initialization_methods[group_by]()

    for entry in history_data:
        group_value = group_function(int(entry["lastVisitTime"]))
        category = entry["category"]
        domain = get_domain(entry["url"])
        icon = entry.get("icon", f"https://www.google.com/s2/favicons?domain={domain}&sz=48")
        name = domain

        if category not in output_data[group_value]:
            output_data[group_value][category] = {
                "domains": {},
                "totalCategoryVisits": 0
            }

        if domain not in output_data[group_value][category]["domains"]:
            output_data[group_value][category]["domains"][domain] = {"visitCounterTimeRange": 0, "icon": icon, "name": name}

        output_data[group_value][category]["domains"][domain]["visitCounterTimeRange"] += 1
        output_data[group_value][category]["totalCategoryVisits"] += 1

    for group_value, categories in output_data.items():
        for category, data in categories.items():
            domains_list = [{"domain": k, "visitCounterTimeRange": v["visitCounterTimeRange"], "icon": v["icon"],  "name": v["name"]} for k, v in data["domains"].items()]
            output_data[group_value][category]["domains"] = domains_list

    return output_data

def graph_query(group_by_parameter, user_id, from_epoch, to_epoch):
    table = dynamodb.Table('history')
    response = table.scan(
        FilterExpression="user_id = :user_id AND #lastVisitTime BETWEEN :start_date AND :end_date",
        ExpressionAttributeNames={
            "#lastVisitTime": "lastVisitTime"
        },
        ExpressionAttributeValues={
            ":user_id": user_id,
            ":start_date": Decimal(from_epoch),
            ":end_date": Decimal(to_epoch)
        }
    )
    history_data = response['Items']
    result = process_data(group_by_parameter, history_data)
    return result
