from flask import current_app


def run_job(container, command):
    tag = 'latest'

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
