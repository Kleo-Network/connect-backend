from flask import Blueprint, jsonify, current_app
from celery.result import AsyncResult
from .auth_views import token_required
from ..controllers.history import check_user_authenticity, find_by_address_slug
from ..models.celery_task import get_celery_tasks_by_slug, update_celery_task_status, get_all_celery_tasks, CeleryTask
from ...celery.tasks import celery_app

celery_tasks = Blueprint('celery_tasks', __name__)

@celery_tasks.route('/tasks/update_tasks', methods=['POST'])
def update_database_for_backlog_tasks(**kwargs):
    try:
        password = kwargs.get('password')
        if password != os.environ.get('PASSWORD'):
            return jsonify({"error": "Unauthorized"}), 401

        # Fetch all tasks from Celery that have status other than SUCCESS and populate the database
        i = celery_app.control.inspect()
        active_tasks = i.active() or {}
        reserved_tasks = i.reserved() or {}
        
        all_tasks = []
        for worker, tasks in active_tasks.items():
            all_tasks.extend(tasks)
        for worker, tasks in reserved_tasks.items():
            all_tasks.extend(tasks)

        updated_count = 0
        for task in all_tasks:
            task_id = task['id']
            status = task['status']
            if status != 'SUCCESS':
                # Assuming the task contains 'slug' and 'type' information
                slug = task.get('kwargs', {}).get('slug')
                task_type = task.get('name')  # This might need adjustment based on how you store task types
                
                if slug and task_type:
                    celery_task = CeleryTask(slug, task_id, task_type, status)
                    celery_task.save()
                    updated_count += 1

        return jsonify({
            "message": f"Database updated with {updated_count} backlog tasks",
            "updated_count": updated_count
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error in update_database_for_backlog_tasks: {str(e)}")
        return jsonify({"error": "An error occurred while processing the request"}), 500

@celery_tasks.route('/tasks/update_tasks_db', methods=['POST'])
def update_database_for_existing_tasks(**kwargs):
    try:
        password = kwargs.get('password')
        if password != os.environ.get('PASSWORD'):
            return jsonify({"error": "Unauthorized"}), 401

        # Fetch all tasks from the database and update their status
        all_tasks = get_all_celery_tasks()

        updated_count = 0
        deleted_count = 0

        for task in all_tasks:
            celery_task = AsyncResult(task['task_id'], app=celery_app)
            new_status = celery_task.state
            
            if new_status != task['status']:
                updated_task = update_celery_task_status(task['slug'], task['task_id'], new_status)
                if updated_task:
                    updated_count += 1
                else:
                    # Task was deleted (SUCCESS status)
                    deleted_count += 1

        return jsonify({
            "message": "Database tasks updated",
            "updated_count": updated_count,
            "deleted_count": deleted_count
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error in update_database_for_existing_tasks: {str(e)}")
        return jsonify({"error": "An error occurred while processing the request"}), 500

@celery_tasks.route('/tasks/<string:slug>', methods=['GET'])
def get_and_update_celery_tasks(slug, **kwargs):
    try:
        # Authenticate user
        address = find_by_address_slug(slug)
        if not address:
            return jsonify({"error": "User not found"}), 404
        
        passsword = kwargs.get('password')
        if passsword !== os.environ.get('PASSWORD'):
            return
        # Get all tasks for the slug
        tasks = get_celery_tasks_by_slug(slug)

        # Check and update status for each task
        updated_tasks = []
        for task in tasks:
            celery_task = AsyncResult(task['task_id'], app=celery_app)
            new_status = celery_task.state
            
            if new_status != task['status']:
                updated_task = update_celery_task_status(slug, task['task_id'], new_status)
                if updated_task:
                    updated_tasks.append(updated_task)
            else:
                updated_tasks.append(task)

        return jsonify({
            "message": "Celery tasks retrieved and updated successfully",
            "tasks": updated_tasks
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error in get_and_update_celery_tasks: {str(e)}")
        return jsonify({"error": "An error occurred while processing the request"}), 500