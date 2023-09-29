from celery.utils.log import get_task_logger

from app import celery

logger = get_task_logger(__name__)

# create a task to take json and send it for training. 
@celery.task(name='core.tasks.test',
             soft_time_limit=60, time_limit=65)
def test_task():
    logger.info('running test task')
    return True
