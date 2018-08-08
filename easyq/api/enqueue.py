try:
    from ujson import dumps
except ImportError:
    from json import dumps
from flask import Blueprint, current_app, request

from easyq.worker.job import run_job

bp = Blueprint('enqueue', __name__)


@bp.route('/jobs', methods=('POST', ))
def enqueue():
    container = request.form['container']
    command = request.form['command']
    result = current_app.job_queue.enqueue(run_job, container, command)

    return dumps({
        "job": result.id,
        "status": result._status,
    })
