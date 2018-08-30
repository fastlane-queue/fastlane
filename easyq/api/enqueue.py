from uuid import uuid4

from flask import Blueprint, current_app, g, request

from easyq.models.task import Task
from easyq.worker.job import run_job

try:
    from ujson import dumps
except ImportError:
    from json import dumps

bp = Blueprint('enqueue', __name__)


@bp.route('/tasks/<task_id>', methods=('POST', ))
def create_task(task_id):
    image = request.form['image']
    command = request.form['command']

    logger = g.logger.bind(task_id=task_id, image=image, command=command)

    logger.debug('Creating task...')
    task = Task.objects(task_id=task_id).modify(
        image=image, command=command, upsert=True, new=True)
    logger.info('Task created successfully.')

    job_id = str(uuid4())
    logger.debug('Creating job...', job_id=job_id)
    task.create_job(job_id)
    task.save()
    logger.debug('Job created successfully...', job_id=job_id)

    logger.debug('Enqueuing job execution...')
    result = current_app.job_queue.enqueue(
        run_job, task_id, job_id, timeout=-1)
    logger.info('Job execution enqueued successfully.')

    return dumps({
        "taskId": task_id,
        "jobId": job_id,
        "queueJobId": result.id,
        "status": result._status,
    })
