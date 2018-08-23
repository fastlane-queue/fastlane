from unittest.mock import MagicMock

from preggy import expect
from rq import Queue

import easyq.worker.job as worker


def test_run_job(client):
    '''Test run job does not fail if no job available'''
    with client.application.app_context():
        exec_mock = MagicMock()
        client.application.executor = exec_mock()
        result = worker.run_job('container', 'command')
        expect(result).to_be_false()


def test_run_job2(client):
    '''Test run job does not fail if no job in DB'''
    with client.application.app_context():
        queue = Queue(is_async=False, connection=client.application.redis)
        job = queue.enqueue(worker.run_job, 'container', 'command')
        assert job.is_finished
        exec_mock = MagicMock()
        client.application.executor = exec_mock()
        result = worker.run_job('container', 'command')
        expect(result).to_be_false()


# def run_job(container, command):
# tag = 'latest'
# job = get_current_job(current_app.redis)

# if ':' in container:
# container, tag = container.split(':')

# print(f'Downloading updated container image ({container}:{tag})...')
# current_app.executor.pull(container, tag)

# print(f'Running {command} in {container}:{tag}...')
# job_id = current_app.executor.run(container, tag, command)

# # for line in job.logs(stream=True):
# # print(line.strip())
# # print(current_app.name)
# # print(f'Container: {container} Command: {command}')
