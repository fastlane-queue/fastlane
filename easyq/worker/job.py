from flask import current_app
from rq import get_current_job

from easyq.models.task import Task


def add_task(task_id):
    task = Task.get_by_task_id(task_id)

    job_id = get_current_job().id
    j = task.create_job(job_id)

    return True

    # tag = 'latest'
    # worker_job = get_current_job(current_app.redis)

    # if worker_job is None:
    # return False

    # job = Job.get_by_job_id(worker_job.id)

    # if job is None:
    # return False

    # if ':' in container:
    # container, tag = container.split(':')

    # job.status = Job.Status.pulling
    # job.save()
    # print(f'Downloading updated container image ({container}:{tag})...')
    # current_app.executor.pull(container, tag)

    # print(f'Running {command} in {container}:{tag}...')
    # container_id = current_app.executor.run(container, tag, command)

    # job.container_id = container_id
    # job.status = Job.Status.running
    # job.save()

    # return True
