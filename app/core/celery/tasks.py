from ..modules.history import single_url_request
from ..modules.graph_data import *
from ..controllers.history import *

from celery import shared_task
from celery.contrib.abortable import AbortableTask
import time
from urllib.parse import urlparse
import json
from decimal import Decimal


# @shared_task(name='tasks.process_graph_data')
# def process_graph_data():
#     user = get_user_unprocessed()
    
#     if user:
#         items = process_items(user["id"])
#         batch_insert_items(items)
#         update_user_processed(user["id"], True)

# @shared_task(name='tasks.update_new_history')
# def update_new_history():
#     mark_as_unproccssed()


# create a task to take json and send it for training. 
@shared_task(bind=True, base=AbortableTask)
def categorize_history(self, data): 
    chunk = data["chunk"]
    user_id = data["user_id"]
    for item in chunk:
        domain = urlparse(item["url"]).netloc
        domain_data = domain_exists_or_insert(domain)
        item["domain"] = domain
        item["category"] = domain_data["category"]
        item["category_description"] = domain_data["category_description"]
        item["category_group"] = domain_data["category_group"]
        item["user_id"] = user_id
        item["favourite"] = False
        item["hidden"] = False
        item["visitTime"] = item["lastVisitTime"]
        item = json.loads(json.dumps(item), parse_float=Decimal)
        
    
    upload_browsing_history_chunk(chunk)
    if self.is_aborted():
        return 'Aborted'
    return True


# @celery.task(name='core.tasks.get_icon_from_url')
# def getIcon(item, user_id):
#     extracted = tldextract.extract(item["url"])
#     domain = "{}.{}".format(extracted.domain, extracted.suffix)
#     item["icon"] = "https://www.google.com/s2/favicons?domain={}&sz=48".format(domain)
    
#     return True

    