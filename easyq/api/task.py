from flask import Blueprint, abort, g

from easyq.models.task import Task

try:
    from ujson import dumps
except ImportError:
    from json import dumps

bp = Blueprint('task', __name__)


@bp.route('/tasks/<task_id>/jobs/<job_id>', methods=('GET', ))
def get_job(task_id, job_id):
    logger = g.logger.bind(task_id=task_id, job_id=job_id)

    logger.debug('Getting task...')
    task = Task.objects.get_or_404(task_id=task_id)
    logger.info('Task retrieved successfully.')

    logger.debug('Getting job...')
    job = task.get_job_by_job_id(job_id)

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
