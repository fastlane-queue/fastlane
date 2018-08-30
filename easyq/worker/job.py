from datetime import timedelta

from flask import current_app
from rq_scheduler import Scheduler

from easyq.models.job import Job
from easyq.models.task import Task
from easyq.worker import ExecutionResult


def run_job(task_id, job_id):
    app = current_app
    executor = app.load_executor()

    task = Task.get_by_task_id(task_id)
    job = task.get_job_by_job_id(job_id)
    logger = app.logger.bind(task_id=task_id, job_id=job_id)

    if job is None:
        return False

    image = job.image
    tag = 'latest'

    if ':' in image:
        image, tag = image.split(':')

    logger = logger.bind(image=image, tag=tag)

    logger.debug('Changing job status...', status=Job.Status.pulling)
    job.status = Job.Status.pulling
    task.save()
    logger.debug('Job status changed successfully.', status=Job.Status.pulling)

    logger.info('Downloading updated container image...', image=image, tag=tag)
    executor.pull(image, tag)
    logger.info('Image downloaded successfully.', image=image, tag=tag)

    logger.info(
        'Running command in container...',
        image=image,
        tag=tag,
        command=job.command)
    container_id = executor.run(image, tag, job.command)
    logger.info(
        'Container started successfully.',
        image=image,
        tag=tag,
        command=job.command,
        container_id=container_id)

    logger.debug('Changing job status...', status=Job.Status.running)
    job.container_id = container_id
    job.status = Job.Status.running
    task.save()
    logger.debug('Job status changed successfully.', status=Job.Status.running)

    app.monitor_queue.enqueue(monitor_job, task_id, job_id, timeout=-1)

    return True


def monitor_job(task_id, job_id):
    try:
        app = current_app
        executor = app.load_executor()

        task = Task.get_by_task_id(task_id)
        job = task.get_job_by_job_id(job_id)
        logger = app.logger.bind(task_id=task_id, job_id=job_id)

        if job is None:
            logger.error('Failed to retrieve task or job.')

            return False

        if job.container_id is None:
            logger.error('Job does not have container id. Can\'t proceed.')

            return False

        result = executor.get_result(job.container_id)
        logger.info(
            'Container result obtained.',
            container_status=result.status,
            container_exit_code=result.exit_code)

        if result.status in (ExecutionResult.Status.created,
                             ExecutionResult.Status.running):
            scheduler = Scheduler('monitor', connection=app.redis)
            logger.info(
                'Job has not finished. Retrying monitoring in the future.',
                container_status=result.status,
                seconds=1)

            interval = timedelta(seconds=5)
            scheduler.enqueue_in(interval, monitor_job, task_id, job_id)

            return

        job.status = Job.Status.done
        job.log = result.log.decode('utf-8')
        job.error = result.error.decode('utf-8')

        logger.debug(
            'Job finished. Storing job details in mongo db.',
            status=job.status,
            log=result.log,
            error=result.error,
        )
        job.save()
        logger.info(
            'Job details stored in mongo db.',
            status=job.status,
        )
    except Exception as err:
        logger.error('Failed to monitor job', error=err)
        raise err
