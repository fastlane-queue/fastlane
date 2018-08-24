from uuid import uuid4

from flask import Blueprint, current_app, request

from easyq.models.task import Task
from easyq.worker.job import add_task

try:
    from ujson import dumps
except ImportError:
    from json import dumps

bp = Blueprint('enqueue', __name__)


@bp.route('/tasks', methods=('POST', ))
def create_task():
    container = request.form['container']
    command = request.form['command']

    task_id = str(uuid4())
    Task.create_task(task_id, container, command)

    result = current_app.task_queue.enqueue(add_task, task_id, timeout=-1)

    return dumps({
        "taskId": task_id,
        "jobId": result.id,
        "status": result._status,
    })
