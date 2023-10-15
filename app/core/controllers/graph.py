import json
from datetime import datetime
import boto3
import math
from decimal import Decimal
from collections import OrderedDict
from boto3.dynamodb.conditions import Key, Attr
from ..models.aws_session import dynamodb


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
    'day': group_by_hour,
    'week': group_by_day,
    'month': group_by_week,
    'year': group_by_month
}

def initialize_output_for_hours():
    return OrderedDict([
        ("00-04", {}),
        ("04-08", {}),
        ("08-12", {}),
        ("12-16", {}),
        ("16-20", {}),
        ("20-24", {})
    ])

def initialize_output_for_days():
    return OrderedDict([
        ("Monday", {}),
        ("Tuesday", {}),
        ("Wednesday", {}),
        ("Thursday", {}),
        ("Friday", {}),
        ("Saturday", {}),
        ("Sunday", {})
    ])

def initialize_output_for_weeks():
    return OrderedDict([
        ("Week 1", {}),
        ("Week 2", {}),
        ("Week 3", {}),
        ("Week 4", {}),
        ("Week 5", {})  # Just in case
    ])

def initialize_output_for_year():
    return OrderedDict([
        ("January", {}),
        ("February", {}),
        ("March", {}),
        ("April", {}),
        ("May", {}),
        ("June", {}),
        ("July", {}),
        ("August", {}),
        ("September", {}),
        ("October", {}),
        ("November", {}),
        ("December", {})
    ])

initialization_methods = {
    'day': initialize_output_for_hours,
    'week': initialize_output_for_days,
    'month': initialize_output_for_weeks,
    'year': initialize_output_for_year
}

def process_data_by_domain(group_by, history_data):
    group_function = grouping_methods[group_by]
    output_data = initialization_methods[group_by]()

    for entry in history_data:
        group_value = group_function(int(entry["visitTime"]))
        domain = get_domain(entry["url"])
        icon = entry.get("icon", f"https://www.google.com/s2/favicons?domain={domain}&sz=48")
        name = entry["title"]
        url = entry["url"]
    
        if "urls" not in output_data[group_value]:
            output_data[group_value]["urls"] = []
            output_data[group_value]["visits"] = 0

        url_entry = {
            "icon": icon,
            "title": name,
            "visitTime": Decimal(entry["visitTime"]),
            "url": url,
            "favourite": entry["favourite"]
        }

        # Append the URL entry to the list of URLs for the current group
        output_data[group_value]["urls"].append(url_entry)
        output_data[group_value]["visits"] += 1

    # Remove empty entries:
    output_data = {k: v for k, v in output_data.items() if "urls" in v}

    return output_data


def process_data(group_by, history_data):
    group_function = grouping_methods[group_by]
    output_data = initialization_methods[group_by]()

    for entry in history_data:
        group_value = group_function(int(entry["visitTime"]))
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

def graph_query(group_by_parameter, user_id, from_epoch, to_epoch, domain = None):
    table = dynamodb.Table('history')
    if domain is not None:
        response = table.query(
                            KeyConditionExpression=Key('user_id').eq(user_id) & 
                            Key('visitTime').between(Decimal(from_epoch), Decimal(to_epoch)),
                            FilterExpression="contains(#url_attr, :domain_name)",
                            ExpressionAttributeNames={
                                "#url_attr": "url"
                            },
                            ExpressionAttributeValues={
                                ":domain_name": domain
                            })
        result = process_data_by_domain(group_by_parameter, response['Items'])
    else:
        response = table.query(
                            KeyConditionExpression=Key('user_id').eq(user_id) & 
                            Key('visitTime').between(Decimal(from_epoch), Decimal(to_epoch)))
        result = process_data(group_by_parameter, response['Items'])
    
    return result
