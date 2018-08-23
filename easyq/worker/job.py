from flask import current_app
from rq import get_current_job

from easyq.models.job import Job


def run_job(container, command):
    tag = 'latest'
    worker_job = get_current_job(current_app.redis)

    if worker_job is None:
        return False

    job = Job.get_by_job_id(worker_job.id)

    if job is None:
        return False

    if ':' in container:
        container, tag = container.split(':')

    job.status = Job.Status.pulling
    job.save()
    print(f'Downloading updated container image ({container}:{tag})...')
    current_app.executor.pull(container, tag)

    print(f'Running {command} in {container}:{tag}...')
    container_id = current_app.executor.run(container, tag, command)

    job.container_id = container_id
    job.status = Job.Status.running
    job.save()

    return True
