from flask import Blueprint, current_app, request
from ..controllers.history import *
from werkzeug.local import LocalProxy
from ...celery.tasks import *
from math import ceil
from celery import chord, group
from .auth_views import token_required
from flask import jsonify

core = Blueprint('core', __name__)

logger = LocalProxy(lambda: current_app.logger)


@core.before_request
def before_request_func():
    current_app.logger.name = 'core'
    
