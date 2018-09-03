from flask import Blueprint, abort, g

from easyq.models.job import Job
from easyq.models.task import Task

try:
    from ujson import dumps
except ImportError:
    from json import dumps

bp = Blueprint('task', __name__)


@bp.route('/tasks/<task_id>', methods=('GET', ))
def get_task(task_id):
    logger = g.logger.bind(task_id=task_id)

    logger.debug('Getting job...')
    task = Task.get_by_task_id(task_id)

    if task is None:
        logger.error('Task not found.')
        abort(404)

        return
    logger.debug('Task retrieved successfully...')

    return dumps({
        "taskId": task_id,
        "jobs": [str(j.id) for j in task.jobs],
    })


@bp.route('/tasks/<task_id>/jobs/<job_id>', methods=('GET', ))
def get_job(task_id, job_id):
    logger = g.logger.bind(task_id=task_id, job_id=job_id)

    logger.debug('Getting job...')
    job = Job.get_by_id(task_id=task_id, job_id=job_id)

    if job is None:
        logger.error('Job not found in task.')
        abort(404)

        return
    logger.debug('Job retrieved successfully...')

    return dumps({
        "taskId": task_id,
        "jobId": job_id,
        "details": job.to_dict(include_log=True, include_error=True),
    })
