# Standard Library
import re
from unittest.mock import MagicMock
from uuid import uuid4

# 3rd Party
import pytest
from dateutil.parser import parse
from preggy import expect

# Fastlane
from fastlane.worker.docker_executor import Executor
from tests.fixtures.docker import ClientFixture, ContainerFixture, PoolFixture
from tests.fixtures.models import JobExecutionFixture, TaskFixture


def test_pull1(client):
    """Tests that a docker executor can pull images"""

    with client.application.app_context():
        task_mock = MagicMock()
        job_mock = MagicMock(id=uuid4())
        execution_mock = MagicMock()
        app = MagicMock()
        client = MagicMock()
        pool = MagicMock()
        pool.get_client.return_value = ("localhost", 1010, client)
        exe = Executor(app=app, pool=pool)
        exe.update_image(
            task_mock,
            job_mock,
            execution_mock,
            "mock-image",
            "latest",
            blacklisted_hosts=set(),
        )

        expect(client.images.pull.call_count).to_equal(1)
        client.images.pull.assert_called_with("mock-image", tag="latest")


def test_run1(client):
    """Tests that a docker executor can run containers"""

    with client.application.app_context():
        task_mock = MagicMock()
        job_mock = MagicMock(metadata={})

        execution_mock = MagicMock(
            metadata={"docker_host": "localhost", "docker_port": 1010},
            execution_id=uuid4(),
        )

        app = MagicMock()
        client = MagicMock()
        client.containers.run.return_value = MagicMock(id="job_id")

        pool = MagicMock()
        pool.get_client.return_value = ("localhost", 1010, client)

        exe = Executor(app=app, pool=pool)
        exe.run(
            task_mock,
            job_mock,
            execution_mock,
            "mock-image",
            "latest",
            "command",
            blacklisted_hosts=set(),
        )

        expect(execution_mock.metadata).to_include("container_id")
        expect(client.containers.run.call_count).to_equal(1)
        client.containers.run.assert_called_with(
            image=f"mock-image:latest",
            environment={},
            command="command",
            detach=True,
            name=f"fastlane-job-{execution_mock.execution_id}",
        )


def test_validate_max1(client):
    """
    Tests validating max current executions for a docker host
    """

    app = client.application

    with app.app_context():
        containers = [ContainerFixture.new(name="fastlane-job-123")]
        match, pool_mock, client_mock = PoolFixture.new_defaults(
            r"test.+", max_running=1, containers=containers
        )

        executor = Executor(app, pool_mock)

        result = executor.validate_max_running_executions("test123")
        expect(result).to_be_true()


def test_validate_max2(client):
    """
    Tests validating max current executions works even if no hosts match task_id
    """

    app = client.application

    with app.app_context():
        pool_mock = PoolFixture.new()
        executor = Executor(app, pool_mock)

        result = executor.validate_max_running_executions("test123")
        expect(result).to_be_true()


def test_validate_max3(client):
    """
    Tests validating max current executions returns False
    if max concurrent containers already running
    """

    app = client.application

    with app.app_context():
        containers = [
            ContainerFixture.new(name="fastlane-job-123"),
            ContainerFixture.new(name="fastlane-job-456"),
        ]

        match, pool_mock, client_mock = PoolFixture.new_defaults(
            r"test.+", max_running=1, containers=containers
        )
        executor = Executor(app, pool_mock)

        result = executor.validate_max_running_executions("test123")
        expect(result).to_be_false()


def test_get_result1(client):
    """
    Tests getting container result returns status, exit_code and log when running
    """

    app = client.application

    with app.app_context():
        match, pool_mock, client_mock = PoolFixture.new_defaults(
            r"test[-].+", max_running=1
        )

        started_at = "2018-08-27T17:14:14.1951232Z"
        container_mock = ContainerFixture.new_with_status(
            name="fastlane-job-123",
            status="running",
            started_at=started_at,
            custom_error="custom error",
        )
        client_mock.containers.get.return_value = container_mock

        executor = Executor(app, pool_mock)

        task, job, execution = JobExecutionFixture.new_defaults()

        result = executor.get_result(task, job, execution)
        expect(result.status).to_equal("running")
        expect(result.exit_code).to_be_null()
        expect(result.log).to_be_empty()
        expect(result.error).to_equal("custom error")
        dt = parse(started_at)
        expect(result.started_at).to_equal(dt)
        expect(result.finished_at).to_be_null()


def test_get_result2(client):
    """
    Tests getting container result returns status, exit_code,
    stdout and stderr when successful
    """

    app = client.application

    with app.app_context():
        match, pool_mock, client_mock = PoolFixture.new_defaults(
            r"test[-].+", max_running=1
        )

        started_at = "2018-08-27T17:14:14.1951232Z"
        finished_at = "2018-08-27T17:14:18.1951232Z"
        container_mock = ContainerFixture.new_with_status(
            name="fastlane-job-123",
            status="exited",
            exit_code=0,
            started_at=started_at,
            finished_at=finished_at,
            custom_error="",
            stdout="some log",
            stderr="some error",
        )
        client_mock.containers.get.return_value = container_mock

        executor = Executor(app, pool_mock)

        task, job, execution = JobExecutionFixture.new_defaults()

        result = executor.get_result(job.task, job, execution)
        expect(result.status).to_equal("done")
        expect(result.exit_code).to_equal(0)
        expect(result.log).to_equal("some log")
        expect(result.error).to_equal("some error")
        dt = parse(started_at)
        expect(result.started_at).to_equal(dt)
        dt = parse(finished_at)
        expect(result.finished_at).to_equal(dt)


def test_get_result3(client):
    """
    Tests getting container result returns status, exit_code, stdout and stderr when failed
    """

    with client.application.app_context():
        pytest.skip("Not implemented")


def test_get_result4(client):
    """
    Tests getting container result returns status, exit_code, stdout and
    stderr when failed with previous error
    """

    with client.application.app_context():
        pytest.skip("Not implemented")


def test_stop1(client):
    """
    Tests stopping a job stops the container in docker
    """

    with client.application.app_context():
        pytest.skip("Not implemented")


def test_circuit1(client):
    """
    Tests that when updating with a docker host that's not accessible,
    the circuit is open and a HostUnavailableError is raised
    """

    with client.application.app_context():
        pytest.skip("Not implemented")


def test_circuit2(client):
    """
    Tests that when running a container with a docker host that's not accessible,
    the circuit is open, the host and port are removed from the job's metadata
    and a HostUnavailableError is raised
    """

    with client.application.app_context():
        pytest.skip("Not implemented")


def test_circuit3(client):
    """
    Tests that when monitoring a container with a docker host that's not accessible,
    the circuit is open and a HostUnavailableError is raised
    """

    with client.application.app_context():
        pytest.skip("Not implemented")


def test_circuit4(client):
    """
    Tests that when stopping a container with a docker host that's not accessible,
    the circuit is open and a HostUnavailableError is raised
    """

    with client.application.app_context():
        pytest.skip("Not implemented")


def test_circuit5(client):
    """
    Tests that when getting the result for a container with a
    docker host that's not accessible, the circuit is open and
    a HostUnavailableError is raised
    """

    with client.application.app_context():
        pytest.skip("Not implemented")


def test_circuit6(client):
    """
    Tests that when getting streaming logs with a
    docker host that's not accessible, the circuit is open and
    a HostUnavailableError is raised
    """

    with client.application.app_context():
        pytest.skip("Not implemented")


def test_circuit7(client):
    """
    Tests that when marking a container as done with a
    docker host that's not accessible, the circuit is open and
    a HostUnavailableError is raised
    """

    with client.application.app_context():
        pytest.skip("Not implemented")


def test_pool1(client):
    """
    Tests that when getting docker hosts, hosts with open circuits are not returned
    """

    with client.application.app_context():
        pytest.skip("Not implemented")


def test_pool2(client):
    """
    Tests that when getting docker hosts, hosts with half-open circuits are returned
    """

    with client.application.app_context():
        pytest.skip("Not implemented")


def test_pool3(client):
    """
    Tests that when getting docker hosts, the circuit is refreshed
    """

    with client.application.app_context():
        pytest.skip("Not implemented")


def test_pool4(client):
    """
    Tests that when creating docker executor, the pool is configured properly
    """

    with client.application.app_context():
        pytest.skip("Not implemented")


def test_get_running1(client):
    """
    Tests getting running containers
    """

    with client.application.app_context():
        pytest.skip("Not implemented")


def test_get_running2(client):
    """
    Tests getting running containers when some hosts are unavailable
    """

    with client.application.app_context():
        pytest.skip("Not implemented")


def test_get_running3(client):
    """
    Tests getting running containers when some hosts are blacklisted
    """

    with client.application.app_context():
        pytest.skip("Not implemented")


def test_get_running4(client):
    """
    Tests getting running containers when some circuits are open
    """

    with client.application.app_context():
        pytest.skip("Not implemented")


def test_get_current_logs1(client):
    """
    Tests getting logs for a containers' stderr and stdout
    """

    with client.application.app_context():
        pytest.skip("Not implemented")


def test_get_blacklisted_hosts(client):
    """
    Tests getting the blacklisted hosts
    """

    with client.application.app_context():
        pytest.skip("Not implemented")


def test_mark_as_done1(client):
    """
    Tests marking a container as done renames the container
    """

    with client.application.app_context():
        pytest.skip("Not implemented")


def test_remove_done1(client):
    """
    Tests removing all defunct containers
    """

    with client.application.app_context():
        pytest.skip("Not implemented")
