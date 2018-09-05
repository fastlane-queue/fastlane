from flask import Blueprint, current_app, g, make_response, request

from easyq.models.task import Task
from easyq.worker.job import run_job

try:
    from ujson import dumps
except ImportError:
    from json import dumps

bp = Blueprint('enqueue', __name__)


@bp.route('/tasks/<task_id>', methods=('POST', ))
def create_task(task_id):
    details = request.json
    image = details.get('image', None)
    command = details.get('command', None)

    if image is None or command is None:
        return make_response(
            'image and command must be filled in the request.',
            400,
        )

    logger = g.logger.bind(task_id=task_id, image=image, command=command)

    logger.debug('Creating task...')
    task = Task.objects(task_id=task_id).modify(
        image=image, command=command, upsert=True, new=True)
    logger.info('Task created successfully.')

    logger.debug('Creating job...')
    j = task.create_job()
    job_id = str(j.id)
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
