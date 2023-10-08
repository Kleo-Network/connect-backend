from ..modules.history import single_url_request
from ..models.history import upload_browsing_data, domain_exists_or_insert

from celery import shared_task 
from celery.contrib.abortable import AbortableTask
import time
from urllib.parse import urlparse

# create a task to take json and send it for training. 
@shared_task(bind=True, base=AbortableTask)
def categorize_history(self, data): 
    item = data["item"]
    user_id = data["user_id"]
    domain = urlparse(item["url"]).netloc
    domain_data = domain_exists_or_insert(domain)
    item["domain"] = domain
    item["category"] = domain_data["category"]
    item["category_description"] = domain_data["category_description"]
    item["category_group"] = domain_data["category_group"]
    upload_browsing_data(item, user_id)
    if self.is_aborted():
        return 'Aborted'
    return True

# @celery.task(name='core.tasks.get_icon_from_url')
# def getIcon(item, user_id):
#     extracted = tldextract.extract(item["url"])
#     domain = "{}.{}".format(extracted.domain, extracted.suffix)
#     item["icon"] = "https://www.google.com/s2/favicons?domain={}&sz=48".format(domain)
    
#     return True

    