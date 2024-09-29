from flask import Blueprint, current_app, request, jsonify
from ..controllers.history import *
from werkzeug.local import LocalProxy
from ...celery.tasks import *
from math import ceil
from celery import chord, group
from .auth_views import token_required

core = Blueprint("core", __name__)
logger = LocalProxy(lambda: current_app.logger)


@core.before_request
def before_request_func():
    """Set logger name for the current request context."""
    current_app.logger.name = "core"


@core.route("/upload", methods=["POST"])
@token_required
def upload(**kwargs):
    """
    Endpoint to upload history data and categorize it.
    Requires token authentication.
    """
    data = request.get_json()
    history = data.get("history")
    slug = data.get("slug")

    # Validate required parameters
    if not all([slug, history]):
        return jsonify({"error": "Missing required parameters"}), 400

    # Check if user exists
    result = find_by_address_slug_first_time(slug)
    if result is None:
        return jsonify({"error": "User is not found"}), 401

    address, signup = result

    # Validate user authenticity
    address_from_token = kwargs.get("user_data")["payload"]["publicAddress"]
    if not check_user_authenticity(address, address_from_token):
        return jsonify({"error": "User is not authorized"}), 401

    # Split history into chunks
    chunks = [history[i : i + 50] for i in range(0, len(history), 50)]
    categorize_tasks = [
        categorize_history.s({"chunk": chunk, "slug": slug}) for chunk in chunks
    ]

    # Execute tasks based on signup status
    if signup:
        callback = create_pending_card.s(slug)
        chord(categorize_tasks)(callback)
    else:
        group(categorize_tasks).apply_async()

    return jsonify({"message": "History Upload and Categorization is queued!"}), 202
