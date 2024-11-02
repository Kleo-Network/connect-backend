import requests
import os


def upload_to_arweave(json_object):
    try:
        # Send POST request
        url = os.getenv("BACKEND_UPLOAD_URL")
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json={"data": json_object}, headers=headers)
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            # print("Upload successful. URL:", result["url"])
            return result["url"]
        else:
            print("Error:", response.status_code, response.text)
            return False
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)


def prepare_history_json(history_items, address, user):
    activities = {}
    items = {"content": []}
    from_stamp = float("inf")
    to_stamp = 0
    points = int(user["kleo_points"]) if user else 0

    for item in history_items:
        activities[item["category"]] = activities.get(item["category"], 0) + 1

        # Handle summary fallback to title
        items["content"].append(item.get("summary", "NO CONTENT"))
        items["content"].append(item.get("url", "NO URL"))
        items["content"].append(item.get("title", "NO TITLE"))

        from_stamp = min(from_stamp, item["visitTime"])
        to_stamp = max(to_stamp, item["visitTime"])

        points += 1

    previous_hash = user.get("previous_hash", "") if user else ""

    json_object = {
        "activities": activities,
        "items": items,
        "points": points,
        "fromStamp": from_stamp,
        "toStamp": to_stamp,
        "previous_hash": previous_hash,
    }

    return json_object
