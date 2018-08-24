from flask import Blueprint
from rq import Queue

bp = Blueprint('rq', __name__)


def init_app(app):
    app.task_queue = Queue('tasks', connection=app.redis)
    app.job_queue = Queue('jobs', connection=app.redis)
    app.monitor_queue = Queue('monitor', connection=app.redis)
