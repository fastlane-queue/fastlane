from flask import Blueprint

from flask_rq2 import RQ

rq = RQ()

bp = Blueprint('rq', __name__)


def init_app(app):
    rq.init_app(app)

    app.task_queue = rq.get_queue('tasks')
    app.job_queue = rq.get_queue('jobs')
    app.monitor_queue = rq.get_queue('monitor')
