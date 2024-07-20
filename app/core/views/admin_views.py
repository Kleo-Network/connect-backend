from flask import Blueprint, jsonify, current_app, request
from celery.result import AsyncResult
from .auth_views import token_required
from ..models.user import find_by_address_slug, get_all_users_with_count
from ..models.celery_tasks import get_celery_tasks_by_slug, update_celery_task_status, get_all_celery_tasks, CeleryTask
from celery import current_app as current_celery_app
import os
from ..modules.cards import process_slug
from celery import group
from functools import partial

core = Blueprint('core', __name__)

@core.route('/tasks/update_tasks', methods=['POST'])
def update_database_for_backlog_tasks(**kwargs):
    try:
        print(kwargs.get('password'))
        password = kwargs.get('password')
        print(os.environ.get('PASSWORD'))
        if password != os.environ.get('PASSWORD'):
            return jsonify({"error": "Unauthorized"}), 401

        # Fetch all tasks from Celery that have status other than SUCCESS and populate the database
        i = current_celery_app.celery.control.inspect()
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

@core.route('/tasks/start_history_all', methods=['POST'])
def start_history_all():
    try:
        data = request.get_json()
        slugs = data.get('slugs', [])
        print(slugs)
        if slugs:
            tasks = [process_slug(slug) for slug in slugs]
            print(tasks)
        else:
            result = get_all_users_with_count()
            print(result)
            tasks = [process_slug(user['slug'], min_count=15) for user in result.get("users", [])]
            print(tasks)
        group(tasks)()

        return jsonify({"status": "success", "message": "Tasks queued successfully"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
        

@core.route('/tasks/update_tasks_db', methods=['POST'])
def update_database_for_existing_tasks(**kwargs):
    try:
        print(os.environ.get('PASSWORD'))
        print(kwargs)
        data = request.get_json()
        password = data.get("password", "hello")
        print(password)
        if password != os.environ.get('PASSWORD'):
            return jsonify({"error": "Unauthorized"}), 401

        # Fetch all tasks from the database and update their status
        all_tasks = get_all_celery_tasks()

        updated_count = 0
        deleted_count = 0

        for task in all_tasks:
            celery_task = AsyncResult(task['task_id'], app=current_celery_app)
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

@core.route('/tasks/<string:slug>', methods=['GET'])
def get_and_update_celery_tasks(slug, **kwargs):
    try:
        # Authenticate user
        address = find_by_address_slug(slug)
        if not address:
            return jsonify({"error": "User not found"}), 404
        
        passsword = request.args.get('password')
        if passsword != os.environ.get('PASSWORD'):
            return
        # Get all tasks for the slug
        tasks = get_celery_tasks_by_slug(slug)
        

        # Check and update status for each task
        updated_tasks = []
        
        for task in tasks:
            celery_task = AsyncResult(task['task_id'], app=current_celery_app)
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