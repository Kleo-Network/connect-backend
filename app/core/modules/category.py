import requests
from bs4 import BeautifulSoup as bs
import json
from urllib.parse import urlparse
import time


def get_category(raw_resp):
    soup = bs(raw_resp.text)
    result = soup.find("div", {"id": "webfilter-result"})
    paragraph = result.select_one("div > p").getText()
    main_result = result.find("h4", {"class": "info_title"})
    category_description = paragraph.split("Group:")[0]
    category_group = paragraph.split("Group:")[1]
    category = main_result.getText()
    time.sleep(1)

    return category_group, category_description, category


def single_url_request(main_url, item):
    url = "https://www.fortiguard.com/webfilter"
    payload = {"url": main_url}
    response = requests.request("POST", url, headers={}, data=payload, files=[])
    category_group, category_description, category = get_category(response)
    item["category_group"] = category_group
    item["category_description"] = category_description
    item["category"] = category
    return item
