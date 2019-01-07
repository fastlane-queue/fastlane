# Standard Library
from unittest.mock import MagicMock
from uuid import uuid4

# 3rd Party
import pytest
from preggy import expect

# Fastlane
from fastlane.worker.docker_executor import Executor


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

    pytest.skip("Not implemented")


def test_validate_max2(client):
    """
    Tests validating max current executions works even if no hosts match task_id
    """

    pytest.skip("Not implemented")


def test_get_result1(client):
    """
    Tests getting container result returns status, exit_code and log when successful
    """

    pytest.skip("Not implemented")


def test_get_result2(client):
    """
    Tests getting container result returns status, exit_code and log when failed
    """

    pytest.skip("Not implemented")


def test_stop1(client):
    """
    Tests stopping a job stops the container in docker
    """

    pytest.skip("Not implemented")


def test_circuit1(client):
    """
    Tests that when updating with a docker host that's not accessible,
    the circuit is open and a HostUnavailableError is raised
    """

    pytest.skip("Not implemented")


def test_circuit2(client):
    """
    Tests that when running a container with a docker host that's not accessible,
    the circuit is open, the host and port are removed from the job's metadata
    and a HostUnavailableError is raised
    """

    pytest.skip("Not implemented")


def test_circuit3(client):
    """
    Tests that when monitoring a container with a docker host that's not accessible,
    the circuit is open and a HostUnavailableError is raised
    """

    pytest.skip("Not implemented")


def test_circuit4(client):
    """
    Tests that when stopping a container with a docker host that's not accessible,
    the circuit is open and a HostUnavailableError is raised
    """

    pytest.skip("Not implemented")


def test_circuit5(client):
    """
    Tests that when getting the result for a container with a
    docker host that's not accessible, the circuit is open and
    a HostUnavailableError is raised
    """

    pytest.skip("Not implemented")


def test_circuit6(client):
    """
    Tests that when getting streaming logs with a
    docker host that's not accessible, the circuit is open and
    a HostUnavailableError is raised
    """

    pytest.skip("Not implemented")


def test_circuit7(client):
    """
    Tests that when marking a container as done with a
    docker host that's not accessible, the circuit is open and
    a HostUnavailableError is raised
    """

    pytest.skip("Not implemented")


def test_pool1(client):
    """
    Tests that when getting docker hosts, hosts with open circuits are not returned
    """

    pytest.skip("Not implemented")


def test_pool2(client):
    """
    Tests that when getting docker hosts, hosts with half-open circuits are returned
    """

    pytest.skip("Not implemented")


def test_pool3(client):
    """
    Tests that when getting docker hosts, the circuit is refreshed
    """

    pytest.skip("Not implemented")


def test_get_running1(client):
    """
    Tests getting running containers
    """

    pytest.skip("Not implemented")


def test_get_running2(client):
    """
    Tests getting running containers when some hosts are unavailable
    """

    pytest.skip("Not implemented")


def test_get_running3(client):
    """
    Tests getting running containers when some hosts are blacklisted
    """

    pytest.skip("Not implemented")


def test_get_running4(client):
    """
    Tests getting running containers when some circuits are open
    """

    pytest.skip("Not implemented")


def test_get_current_logs1(client):
    """
    Tests getting logs for a containers' stderr and stdout
    """

    pytest.skip("Not implemented")


def test_get_blacklisted_hosts(client):
    """
    Tests getting the blacklisted hosts
    """

    pytest.skip("Not implemented")


def test_mark_as_done1(client):
    """
    Tests marking a container as done renames the container
    """

    pytest.skip("Not implemented")


def test_remove_done1(client):
    """
    Tests removing all defunct containers
    """

    pytest.skip("Not implemented")
