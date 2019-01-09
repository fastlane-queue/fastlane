# Standard Library
from unittest.mock import MagicMock

# 3rd Party
import docker
import pytest
from dateutil.parser import parse
from preggy import expect

# Fastlane
from fastlane.worker.docker_executor import STATUS, DockerPool, Executor
from tests.fixtures.docker import ContainerFixture, PoolFixture
from tests.fixtures.models import JobExecutionFixture


def test_pull1(client):
    """Tests that a docker executor can pull images"""

    with client.application.app_context():
        task, job, execution = JobExecutionFixture.new_defaults()
        match, pool_mock, client_mock = PoolFixture.new_defaults(r"test-.+")

        exe = Executor(app=client.application, pool=pool_mock)
        exe.update_image(
            task, job, execution, "mock-image", "latest", blacklisted_hosts=set()
        )

        expect(client_mock.images.pull.call_count).to_equal(1)
        client_mock.images.pull.assert_called_with("mock-image", tag="latest")


def test_run1(client):
    """Tests that a docker executor can run containers"""

    with client.application.app_context():
        task, job, execution = JobExecutionFixture.new_defaults()
        match, pool_mock, client_mock = PoolFixture.new_defaults(r"test-.+")

        client_mock.containers.run.return_value = MagicMock(id="job_id")

        exe = Executor(app=client.application, pool=pool_mock)
        exe.run(
            task,
            job,
            execution,
            "mock-image",
            "latest",
            "command",
            blacklisted_hosts=set(),
        )

        expect(execution.metadata).to_include("container_id")
        expect(client_mock.containers.run.call_count).to_equal(1)
        client_mock.containers.run.assert_called_with(
            image=f"mock-image:latest",
            environment={},
            command="command",
            detach=True,
            name=f"fastlane-job-{execution.execution_id}",
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
    Tests getting container result returns status, exit_code and log
    """

    # status, exit_code, stdout, stderr, custom_error, started_at, finished_at
    cases = (
        (
            "running",  # status
            None,  # exit_code
            None,  # stdout
            None,  # stderr
            "custom error",  # custom_error
            "2018-08-27T17:14:14.1951232Z",  # started_at
            None,  # finished_at
        ),
        (
            "exited",  # status
            0,  # exit_code
            "some log",  # stdout
            "some error",  # stderr
            "",  # custom_error
            "2018-08-27T17:14:14.1951232Z",  # started_at
            "2018-08-27T17:14:17.1951232Z",  # finished_at
        ),
        (
            "dead",  # status
            1,  # exit_code
            "some log",  # stdout
            "some error",  # stderr
            "",  # custom_error
            "2018-08-27T17:14:14.1951232Z",  # started_at
            "2018-08-27T17:14:17.1951232Z",  # finished_at
        ),
        (
            "dead",  # status
            1,  # exit_code
            "some log",  # stdout
            "some error",  # stderr
            "previous",  # custom_error
            "2018-08-27T17:14:14.1951232Z",  # started_at
            "2018-08-27T17:14:17.1951232Z",  # finished_at
        ),
    )

    for case in cases:
        verify_get_result(client, *case)


def verify_get_result(
    client, status, exit_code, stdout, stderr, custom_error, started_at, finished_at
):
    app = client.application

    with app.app_context():
        match, pool_mock, client_mock = PoolFixture.new_defaults(
            r"test[-].+", max_running=1
        )

        container_mock = ContainerFixture.new_with_status(
            name="fastlane-job-123",
            status=status,
            exit_code=exit_code,
            started_at=started_at,
            finished_at=finished_at,
            custom_error=custom_error,
            stdout=stdout,
            stderr=stderr,
        )
        client_mock.containers.get.return_value = container_mock

        executor = Executor(app, pool_mock)

        task, job, execution = JobExecutionFixture.new_defaults()

        result = executor.get_result(job.task, job, execution)
        expect(result.status).to_equal(STATUS.get(status))
        expect(result.exit_code).to_equal(exit_code)

        if stdout is None:
            expect(result.log).to_be_empty()
        else:
            expect(result.log).to_equal(stdout)

        if stderr is not None and custom_error != "":
            expect(result.error).to_equal(f"{custom_error}\n\nstderr:\n{stderr}")
        else:
            if stderr is not None:
                expect(result.error).to_equal(stderr)
            else:
                expect(result.error).to_equal(custom_error)

        dt = parse(started_at)
        expect(result.started_at).to_equal(dt)

        if finished_at is not None:
            dt = parse(finished_at)
        else:
            dt = finished_at
        expect(result.finished_at).to_equal(dt)


def test_stop1(client):
    """
    Tests stopping a job stops the container in docker
    """

    app = client.application

    with app.app_context():
        match, pool_mock, client_mock = PoolFixture.new_defaults(
            r"test[-].+", max_running=1
        )

        container_mock = ContainerFixture.new_with_status(name="fastlane-job-1234")
        client_mock.containers.get.return_value = container_mock

        task, job, execution = JobExecutionFixture.new_defaults(
            container_id="fastlane-job-1234"
        )

        executor = Executor(app, pool_mock)

        executor.stop_job(task, job, execution)
        container_mock.stop.assert_called()


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
        pool = DockerPool(([None, ["localhost:1234", "localhost:4567"], 2],))
        executor = Executor(client.application, pool)
        executor.get_circuit("localhost:4567").open()

        host, port, client = pool.get_client(executor, "test-123")
        expect(host).to_equal("localhost")
        expect(port).to_equal(1234)


def test_pool2(client):
    """
    Tests that when getting docker hosts, hosts with half-open circuits are returned
    """

    with client.application.app_context():
        pool = DockerPool(([None, ["localhost:1234"], 2],))
        executor = Executor(client.application, pool)
        executor.get_circuit("localhost:1234").half_open()

        host, port, client = pool.get_client(executor, "test-123")
        expect(host).to_equal("localhost")
        expect(port).to_equal(1234)


def test_pool3(client):
    """
    Tests that when creating docker executor, the pool is configured properly
    """

    with client.application.app_context():
        executor = Executor(client.application)
        pool = executor.pool
        expect(pool.clients).to_include("localhost:2375")

        host, port, client = pool.clients["localhost:2375"]
        expect(host).to_equal("localhost")
        expect(port).to_equal(2375)
        expect(client).to_be_instance_of(docker.client.DockerClient)

        expect(pool.max_running).to_equal({None: 2})


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
