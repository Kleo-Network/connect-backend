from ..modules.history import single_url_request
from ..modules.graph_data import *
from ..controllers.history import *

from celery import shared_task
from celery.contrib.abortable import AbortableTask
import time
from urllib.parse import urlparse
import json
from decimal import Decimal

@shared_task(name='tasks.test_task')
def test_task(task_results, user_id):
    print(user_id)
    print(task_results)
    print("test task executed after uploading everything, right?")

@shared_task(name='tasks.process_pinned_graph_data', base=AbortableTask)
def process_pinned_graph_data(user,domain):
    for counter in range(1,180):
        process_pinned_domain_items_for_graph.delay(user,domain,counter)

@shared_task(name='tasks.process_graph_data', base=AbortableTask)
def process_graph_data(params):
    user_id = params["user_id"]
    signup = params["signup"]
    if signup is False and user_id is None:
        user_details = get_user_unprocessed_graph()
        user_id = user_details["id"]
        process_items(user_id)
    else:
        if user_id is not None:
            process_items(user_id,0)
            for counter in range(1, 180):
                process_items(user_id, counter)
        

@shared_task(name='tasks.update_new_history')
def update_new_history_graph_data():
    mark_as_unproccssed('process_graph')

@shared_task(name='tasks.update_new_history_pinned')
def update_new_history_pinned():
    mark_as_unproccssed('process_graph_pinned')

@shared_task(base=AbortableTask)
def process_items_for_graph(user, counter):
    process_items(user, counter)

@shared_task(base=AbortableTask)
def process_pinned_domain_items_for_graph(user, domain,day_start):
    process_items_pinned_data(user, domain,day_start)

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

    