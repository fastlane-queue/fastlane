from unittest.mock import MagicMock

from preggy import expect

from fastlane.worker.docker_executor import Executor


def test_pull(client):
    """Tests that a docker executor can pull images"""
    task_mock = MagicMock()
    job_mock = MagicMock()
    execution_mock = MagicMock()
    app = MagicMock()
    client = MagicMock()
    pool = MagicMock()
    pool.get_client.return_value = ("localhost", 1010, client)
    exe = Executor(app=app, pool=pool)
    exe.update_image(task_mock, job_mock, execution_mock, "mock-image", "latest")

    expect(client.images.pull.call_count).to_equal(1)
    client.images.pull.assert_called_with("mock-image", tag="latest")


def test_run(client):
    """Tests that a docker executor can run containers"""

    task_mock = MagicMock()
    job_mock = MagicMock(metadata={})

    execution_mock = MagicMock(
        metadata={"docker_host": "localhost", "docker_port": 1010}
    )

    app = MagicMock()
    client = MagicMock()
    client.containers.run.return_value = MagicMock(id="job_id")

    pool = MagicMock()
    pool.get_client.return_value = ("localhost", 1010, client)

    exe = Executor(app=app, pool=pool)
    exe.run(task_mock, job_mock, execution_mock, "mock-image", "latest", "command")

    expect(execution_mock.metadata).to_include("container_id")
    expect(client.containers.run.call_count).to_equal(1)
    client.containers.run.assert_called_with(
        image=f"mock-image:latest", environment={}, command="command", detach=True
    )
