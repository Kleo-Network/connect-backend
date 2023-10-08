import requests
from bs4 import BeautifulSoup as bs
import json
from urllib.parse import urlparse
import time

def get_category(raw_resp):
    try:
        soup = bs(raw_resp.text)
        result = soup.find("div", {"id": "webfilter-result"})
        paragraph = result.select_one("div > p").getText()
        main_result = result.find("h4", {"class": "info_title"})
        category_description = paragraph.split("Group:")[0].strip()
        category_group = paragraph.split("Group:")[1].strip()
        category = main_result.getText().split("Category:")[1].strip()
        return category_group, category_description, category
    except:
        return "Other", "Unknown", "Other"


def single_url_request(domain):
    url = "https://www.fortiguard.com/webfilter"
    print(domain)
    payload = {'url': domain}
    response = requests.request("POST", url, headers={}, data=payload, files=[])
    return get_category(response)