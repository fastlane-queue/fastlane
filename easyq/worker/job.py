from flask import current_app
from rq import get_current_job


def run_job(container, command):
    tag = 'latest'
    job = get_current_job(current_app.redis)

    if ':' in container:
        container, tag = container.split(':')

    print(f'Downloading updated container image ({container}:{tag})...')
    current_app.executor.pull(container, tag)

    print(f'Running {command} in {container}:{tag}...')
    job_id = current_app.executor.run(container, tag, command)

    # for line in job.logs(stream=True):
    # print(line.strip())
    # print(current_app.name)
    # print(f'Container: {container} Command: {command}')
