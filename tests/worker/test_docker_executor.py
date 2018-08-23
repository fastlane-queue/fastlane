from unittest.mock import MagicMock

from preggy import expect

from easyq.worker.docker_executor import Executor


def test_pull(client):
    '''Tests that a docker executor can pull images'''
    app = MagicMock()
    client = MagicMock()
    exe = Executor(app=app, client=client)
    exe.pull("mock-image", "latest")

    expect(client.images.pull.call_count).to_equal(1)
    client.images.pull.assert_called_with("mock-image", tag="latest")


def test_run(client):
    '''Tests that a docker executor can run containers'''

    app = MagicMock()
    client = MagicMock()
    client.containers.run.return_value = MagicMock(id='job_id')

    exe = Executor(app=app, client=client)
    job_id = exe.run("mock-image", "latest", "command")

    expect(job_id).to_equal('job_id')
    expect(client.containers.run.call_count).to_equal(1)
    client.containers.run.assert_called_with(
        image=f'mock-image:latest', command='command', detach=True)
