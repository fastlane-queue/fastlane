# Standard Library
from datetime import datetime, timedelta
from unittest.mock import MagicMock

# 3rd Party
import pytest
from preggy import expect
from rq import Queue, SimpleWorker
from tests.fixtures.models import JobExecutionFixture

# Fastlane
import fastlane.worker.job as job_mod
from fastlane.models import JobExecution, Task


def test_run_job1(client):
    """Test running a new job for a task"""
    with client.application.app_context():
        app = client.application
        app.redis.flushall()

        task, job, execution = JobExecutionFixture.new_defaults()

        exec_mock = MagicMock()
        exec_mock.validate_max_running_executions.return_value = True
        client.application.executor = exec_mock

        queue = Queue("jobs", is_async=False, connection=client.application.redis)
        result = queue.enqueue(
            job_mod.run_job,
            task.task_id,
            job.job_id,
            execution.execution_id,
            "image",
            "command",
        )

        worker = SimpleWorker([queue], connection=queue.connection)
        worker.work(burst=True)

        task.reload()
        expect(task.jobs).to_length(1)

        job = task.jobs[0]
        expect(job.executions).to_length(1)

        execution = job.executions[0]
        expect(execution.image).to_equal("image")
        expect(execution.command).to_equal("command")

        hash_key = f"rq:job:{result.id}"

        res = app.redis.exists(hash_key)
        expect(res).to_be_true()

        res = app.redis.hget(hash_key, "status")
        expect(res).to_equal("finished")

        res = app.redis.hexists(hash_key, "data")
        expect(res).to_be_true()

        keys = app.redis.keys()
        next_job_id = [
            key

            for key in keys

            if key.decode("utf-8").startswith("rq:job")
            and not key.decode("utf-8").endswith(result.id)
        ]
        expect(next_job_id).to_length(1)
        next_job_id = next_job_id[0]

        res = app.redis.exists(next_job_id)
        expect(res).to_be_true()

        res = app.redis.hget(next_job_id, "status")
        expect(res).to_equal("queued")

        res = app.redis.hexists(next_job_id, "data")
        expect(res).to_be_true()

        res = app.redis.hget(next_job_id, "origin")
        expect(res).to_equal("monitor")

        res = app.redis.hget(next_job_id, "description")
        expect(res).to_equal(
            f"fastlane.worker.job.monitor_job('{task.task_id}', '{job.job_id}', '{execution.execution_id}')"
        )

        res = app.redis.hget(next_job_id, "timeout")
        expect(res).to_equal("-1")

        task.reload()
        expect(task.jobs[0].executions[0].status).to_equal(JobExecution.Status.running)


def test_validate_max1(client):
    """
    Test validating max concurent executions for a farm returns True
    if max concurrent executions not reached.
    """
    with client.application.app_context():
        pytest.skip("Not implemented")


def test_validate_max2(client):
    """
    Test validating max concurent executions for a farm returns False
    if max concurrent executions reached and re-enqueues the Job.
    """
    with client.application.app_context():
        pytest.skip("Not implemented")


def test_validate_expiration1(client):
    """
    Test validating the expiration of a Job returns True if the job
    has no expiration.
    """
    with client.application.app_context():
        pytest.skip("Not implemented")


def test_validate_expiration2(client):
    """
    Test validating the expiration of a Job returns True if the job
    has expiration but not expired.
    """
    with client.application.app_context():
        pytest.skip("Not implemented")


def test_validate_expiration3(client):
    """
    Test validating the expiration of a Job returns False if the job
    has expiration and has expired. It also tests that the job is marked
    as expired with the proper message as error.
    """
    with client.application.app_context():
        pytest.skip("Not implemented")


def test_reenqueue_job1(client):
    """
    Test re-enqueuing a job due to Executor HostUnavailableError.
    """
    with client.application.app_context():
        pytest.skip("Not implemented")


def test_downloading_image1(client):
    """
    Test updating an image works and returns True
    """
    with client.application.app_context():
        pytest.skip("Not implemented")


def test_downloading_image2(client):
    """
    Test updating an image when executor raises HostUnavailableError,
    the job is re-enqueued and method returns False
    """
    with client.application.app_context():
        pytest.skip("Not implemented")


def test_downloading_image3(client):
    """
    Test updating an image when executor raises any exception other than
    HostUnavailableError, the job is marked as failed with the proper error
    and method returns False
    """
    with client.application.app_context():
        pytest.skip("Not implemented")


def test_run_container1(client):
    """
    Test running a container works and returns True
    """
    with client.application.app_context():
        pytest.skip("Not implemented")


def test_run_container2(client):
    """
    Test running a container when executor raises HostUnavailableError,
    the job is re-enqueued and method returns False
    """
    with client.application.app_context():
        pytest.skip("Not implemented")


def test_run_container3(client):
    """
    Test running a container when executor raises any exception other than
    HostUnavailableError, the job is marked as failed with the proper error
    and method returns False
    """
    with client.application.app_context():
        pytest.skip("Not implemented")


def test_monitor_job_with_retry(client):
    """Test monitoring a job for a task that fails"""

    with client.application.app_context():
        app = client.application
        app.redis.flushall()

        task, job, execution = JobExecutionFixture.new_defaults()
        job.metadata["retries"] = 3
        job.metadata["retry_count"] = 0
        job.save()
        job_id = str(job.job_id)

        exec_mock = MagicMock()
        exec_mock.get_result.return_value = MagicMock(
            exit_code=1, log="".encode("utf-8"), error="error".encode("utf-8")
        )
        client.application.executor = exec_mock

        queue = Queue("monitor", is_async=False, connection=client.application.redis)
        result = queue.enqueue(
            job_mod.monitor_job, task.task_id, job_id, execution.execution_id
        )

        worker = SimpleWorker([queue], connection=queue.connection)
        worker.work(burst=True)

        task.reload()
        expect(task.jobs).to_length(1)

        job = task.jobs[0]
        expect(job.executions).to_length(2)

        execution = job.executions[0]
        expect(execution.image).to_equal("image")
        expect(execution.command).to_equal("command")

        hash_key = f"rq:job:{result.id}"

        res = app.redis.exists(hash_key)
        expect(res).to_be_true()

        res = app.redis.hget(hash_key, "status")
        expect(res).to_equal("finished")

        res = app.redis.hexists(hash_key, "data")
        expect(res).to_be_true()

        res = app.redis.zrange(b"rq:scheduler:scheduled_jobs", 0, -1)
        expect(res).to_length(1)

        time = datetime.now() + timedelta(seconds=2)
        res = app.redis.zscore("rq:scheduler:scheduled_jobs", res[0])
        expect(int(res)).to_be_greater_than(int(time.timestamp()) - 2)
        expect(int(res)).to_be_lesser_than(int(time.timestamp()) + 2)

        new_job = app.redis.zrange("rq:scheduler:scheduled_jobs", 0, 0)[0].decode(
            "utf-8"
        )
        next_job_id = f"rq:job:{new_job}"
        res = app.redis.exists(next_job_id)
        expect(res).to_be_true()

        res = app.redis.hexists(next_job_id, "data")
        expect(res).to_be_true()

        res = app.redis.hget(next_job_id, "origin")
        expect(res).to_equal("jobs")

        res = app.redis.hget(next_job_id, "description")
        job.reload()
        expect(res).to_equal(
            (
                f"fastlane.worker.job.run_job('{task.task_id}', '{job_id}', "
                f"'{job.executions[-1].execution_id}', 'image', 'command')"
            )
        )

        task.reload()
        expect(task.jobs[0].executions[0].status).to_equal(JobExecution.Status.failed)


def test_monitor_job_with_retry2(client):
    """Test monitoring a job for a task that fails stops after max retries"""
    with client.application.app_context():
        app = client.application
        app.redis.flushall()

        task, job, execution = JobExecutionFixture.new_defaults()
        job.metadata["retries"] = 3
        job.metadata["retry_count"] = 3
        job.save()
        job_id = job.job_id

        exec_mock = MagicMock()
        exec_mock.get_result.return_value = MagicMock(
            exit_code=1, log="".encode("utf-8"), error="error".encode("utf-8")
        )
        client.application.executor = exec_mock

        queue = Queue("monitor", is_async=False, connection=client.application.redis)
        result = queue.enqueue(
            job_mod.monitor_job, task.task_id, job_id, execution.execution_id
        )

        worker = SimpleWorker([queue], connection=queue.connection)
        worker.work(burst=True)

        task.reload()
        expect(task.jobs).to_length(1)

        job = task.jobs[0]
        expect(job.executions).to_length(1)

        execution = job.executions[0]
        expect(execution.image).to_equal("image")
        expect(execution.command).to_equal("command")

        hash_key = f"rq:job:{result.id}"

        res = app.redis.exists(hash_key)
        expect(res).to_be_true()

        res = app.redis.hget(hash_key, "status")
        expect(res).to_equal("finished")

        res = app.redis.hexists(hash_key, "data")
        expect(res).to_be_true()

        keys = app.redis.keys()
        next_job_id = [
            key

            for key in keys

            if key.decode("utf-8").startswith("rq:job")
            and not key.decode("utf-8").endswith(result.id)
        ]
        expect(next_job_id).to_length(0)
