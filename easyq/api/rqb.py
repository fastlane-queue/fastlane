from flask import Blueprint
from rq import Queue

bp = Blueprint('rq', __name__)


def init_app(app):
    app.job_queue = Queue('jobs', connection=app.redis)
    app.monitor_queue = Queue('monitor', connection=app.redis)
