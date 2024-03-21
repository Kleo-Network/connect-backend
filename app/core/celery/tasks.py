from ..modules.history import single_url_request
from ..modules.graph_data import *
from ..controllers.history import *
from ..models.history import *
from ..models.user import *

from celery import shared_task
from celery.contrib.abortable import AbortableTask
import time
from urllib.parse import urlparse
import json
from decimal import Decimal

@shared_task(name='task.print', base=AbortableTask)
def print_task():
    print("please print it")

@shared_task(name='tasks.process_graph_data', base=AbortableTask)
def process_graph_data(params=None):
    if params is None:
        user_details = get_user_unprocessed_graph()
        user_id = user_details["id"]
        user = get_process_graph_previous_history(user_id)
        if user["process_graph"] == False and user["process_graph_previous_history"] == True:
            process_items(user_id)
            update_user_processed(user_id, True)
        if user["process_graph_previous_history"] == False:
            for counter in range(0, 90):
                process_items_for_graph_fn.delay(user_id, counter)
            update_user_processed_previous_history(user_id, True)
    elif "signup" in params and "user_id" in params:
        user_id = params["user_id"]
        signup = params["signup"]
        date = params["date"]
        if user_id is not None and signup is True:
            process_items(user_id)
            for index in range(1, counter):
                process_items_for_graph_fn.delay(user_id, date)
            
        

@shared_task(name='tasks.update_new_history')
def update_new_history_graph_data():
    mark_as_unproccssed('process_graph')

@shared_task(name='tasks.process_previous_history')
def upload_history_next_two_days(task_results,slug):
    user = find_by_slug(slug)
    process_date_timestamp = task_results[0]
    print(process_date_timestamp)
    process_date = datetime.utcfromtimestamp(process_date_timestamp)
    current_date = datetime.utcnow()
    difference = (current_date - process_date).days
    print(difference)
    if difference > 2:
        print("more than 2 days difference.")
    

@shared_task(name='tasks.process_items_for_graph',base=AbortableTask)
def process_items_for_graph_fn(user, date):
    process_items(user, date)



# create a task to take json and send it for training. 
@shared_task(bind=True, base=AbortableTask)
def categorize_history(self, data): 
    chunk = data["chunk"]
    slug = data["slug"]
    
    print(f"chunk:{chunk}\nslug: {slug}\n")
    for item in chunk:
        print(item)
        domain = urlparse(item["url"]).netloc
        domain_data = domain_exists_or_insert(domain)
        history = History(slug, item["title"], domain_data["category"], domain_data["category_group"], item["url"], domain, domain_data["category_description"])
        print("view",history)
        history.save()
        
    if self.is_aborted():
        return 'Aborted'
    last_processed_timestamp = datetime.now().timestamp()
    return last_processed_timestamp

@shared_task(name='tasks.process_pinned_graph_data', base=AbortableTask)
def process_pinned_graph_data(user,domain):
    process_items_pinned_data(user,domain)

# @shared_task(base=AbortableTask)
# def process_pinned_domain_items_for_graph(user, domain):
#     process_items_pinned_data(user, domain)
# @celery.task(name='core.tasks.get_icon_from_url')
# def getIcon(item, user_id):
#     extracted = tldextract.extract(item["url"])
#     domain = "{}.{}".format(extracted.domain, extracted.suffix)
#     item["icon"] = "https://www.google.com/s2/favicons?domain={}&sz=48".format(domain)
    
#     return True

    