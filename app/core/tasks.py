from celery.utils.log import get_task_logger
from .history import single_url_request
from .database import upload_browsing_data
from app import celery

logger = get_task_logger(__name__)

# create a task to take json and send it for training. 
@celery.task(name='core.tasks.categorize_history')
def categorize_history(item, user_id):    
    item = single_url_request(item["url"], item)
    upload_browsing_data(item, user_id)
    logger.info('item uploaded ')
    return True
