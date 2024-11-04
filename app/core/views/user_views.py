from flask import Blueprint, request, jsonify
from ...celery.tasks import (
    update_user_graph_cache,
    contextual_activity_classification_for_batch,
    contextual_activity_classification
)

core = Blueprint("core", __name__)

@core.route("/tasks/update-user-graph", methods=["POST"])
def trigger_update_user_graph():
    try:
        data = request.get_json()
        user_address = data.get("address")
        
        if not user_address:
            return jsonify({"error": "Address is required"}), 400
            
        task = update_user_graph_cache.delay(user_address)
        return jsonify({
            "task_id": task.id,
            "status": "Task started"
        }), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@core.route("/tasks/classify-batch-activity", methods=["POST"])
def trigger_batch_classification():
    try:
        data = request.get_json()
        history = data.get("history")
        user_address = data.get("address")

        if not history or not user_address:
            return jsonify({"error": "Both history and address are required"}), 400

        task = contextual_activity_classification_for_batch.delay(history, user_address)
        return jsonify({
            "task_id": task.id,
            "status": "Task started"
        }), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@core.route("/tasks/classify-single-activity", methods=["POST"])
def trigger_single_classification():
    try:
        data = request.get_json()
        activity_item = data.get("activity")
        user_address = data.get("address")

        if not activity_item or not user_address:
            return jsonify({"error": "Both activity and address are required"}), 400

        task = contextual_activity_classification.delay(activity_item, user_address)
        return jsonify({
            "task_id": task.id,
            "status": "Task started"
        }), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500