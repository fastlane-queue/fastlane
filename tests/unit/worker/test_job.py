# Standard Library
from datetime import datetime, timedelta
from unittest.mock import MagicMock

# 3rd Party
import pytest
from preggy import expect
from tests.fixtures.models import JobExecutionFixture

# Fastlane
import fastlane.worker.job as job_mod
from fastlane.models import JobExecution
from fastlane.models.categories import Categories
from fastlane.queue import Message, Queue


def test_run_job1(worker):
    """Test running a new job for a task"""
    app = worker.app.app

    with app.app_context():
        app.redis.flushall()

        task, job, execution = JobExecutionFixture.new_defaults()

        exec_mock = MagicMock()
        exec_mock.validate_max_running_executions.return_value = True
        app.executor = exec_mock

        queue = app.jobs_queue
        queue.enqueue(
            Categories.Job,
            task.task_id,
            job.job_id,
            execution.execution_id,
            "image",
            "command",
        )

        worker.loop_once()

        task.reload()
        expect(task.jobs).to_length(1)

        job = task.jobs[0]
        expect(job.executions).to_length(1)

        execution = job.executions[0]
        expect(execution.image).to_equal("image")
        expect(execution.command).to_equal("command")

        res = app.redis.llen(queue.queue_name)
        expect(res).to_equal(0)

        task.reload()
        expect(task.jobs[0].executions[0].status).to_equal(JobExecution.Status.running)


def test_validate_max1(worker):
    """
    Test validating max concurent executions for a farm returns True
    if max concurrent executions not reached.
    """
    with worker.app.app.app_context():
        pytest.skip("Not implemented")


def test_validate_max2(worker):
    """
    Test validating max concurent executions for a farm returns False
    if max concurrent executions reached and re-enqueues the Job.
    """
    with worker.app.app.app_context():
        pytest.skip("Not implemented")


def test_validate_expiration1(worker):
    """
    Test validating the expiration of a Job returns True if the job
    has no expiration.
    """
    with worker.app.app.app_context():
        pytest.skip("Not implemented")


def test_validate_expiration2(worker):
    """
    Test validating the expiration of a Job returns True if the job
    has expiration but not expired.
    """
    with worker.app.app.app_context():
        pytest.skip("Not implemented")


def test_validate_expiration3(worker):
    """
    Test validating the expiration of a Job returns False if the job
    has expiration and has expired. It also tests that the job is marked
    as expired with the proper message as error.
    """
    with worker.app.app.app_context():
        pytest.skip("Not implemented")


def test_reenqueue_job1(worker):
    """
    Test re-enqueuing a job due to Executor HostUnavailableError.
    """
    with worker.app.app.app_context():
        pytest.skip("Not implemented")


def test_downloading_image1(worker):
    """
    Test updating an image works and returns True
    """
    with worker.app.app.app_context():
        pytest.skip("Not implemented")


def test_downloading_image2(worker):
    """
    Test updating an image when executor raises HostUnavailableError,
    the job is re-enqueued and method returns False
    """
    with worker.app.app.app_context():
        pytest.skip("Not implemented")


def test_downloading_image3(worker):
    """
    Test updating an image when executor raises any exception other than
    HostUnavailableError, the job is marked as failed with the proper error
    and method returns False
    """
    with worker.app.app.app_context():
        pytest.skip("Not implemented")


def test_run_container1(worker):
    """
    Test running a container works and returns True
    """
    with worker.app.app.app_context():
        pytest.skip("Not implemented")


def test_run_container2(worker):
    """
    Test running a container when executor raises HostUnavailableError,
    the job is re-enqueued and method returns False
    """
    with worker.app.app.app_context():
        pytest.skip("Not implemented")


def test_run_container3(worker):
    """
    Test running a container when executor raises any exception other than
    HostUnavailableError, the job is marked as failed with the proper error
    and method returns False
    """
    with worker.app.app.app_context():
        pytest.skip("Not implemented")


def test_monitor_job1(worker):
    """Test monitoring a job with result already there"""

    app = worker.app.app
    with app.app_context():
        app.redis.flushall()

        task, job, execution = JobExecutionFixture.new_defaults()
        execution.status = JobExecution.Status.running
        job.save()
        job_id = str(job.job_id)

        exec_mock = MagicMock()
        exec_mock.get_result.return_value = MagicMock(
            exit_code=0, log="qwe".encode("utf-8"), error="".encode("utf-8")
        )
        app.executor = exec_mock

        monitor_queue = app.monitor_queue
        monitor_queue.enqueue(
            Categories.Monitor, task.task_id, job_id, execution.execution_id
        )

        worker.loop_once()

        monitor_queue.enqueue(
            Categories.Monitor, task.task_id, job_id, execution.execution_id
        )

        worker.loop_once()

        task.reload()
        expect(task.jobs).to_length(1)

        job = task.jobs[0]
        expect(job.executions).to_length(1)

        execution = job.executions[0]
        expect(execution.image).to_equal("image")
        expect(execution.command).to_equal("command")
        expect(execution.status).to_equal(JobExecution.Status.done)

        expect(app.redis.zcard(Queue.SCHEDULED_QUEUE_NAME)).to_equal(0)


def test_monitor_job_with_retry(worker):
    """Test monitoring a job for a task that fails"""

    app = worker.app.app
    with app.app_context():
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
        app.executor = exec_mock

        monitor_queue = app.monitor_queue
        monitor_queue.enqueue(
            Categories.Monitor, task.task_id, job_id, execution.execution_id
        )

        worker.loop_once()

        task.reload()
        expect(task.jobs).to_length(1)

        job = task.jobs[0]
        expect(job.executions).to_length(2)

        execution = job.executions[0]
        expect(execution.image).to_equal("image")
        expect(execution.command).to_equal("command")

        expect(app.redis.zcard(Queue.SCHEDULED_QUEUE_NAME)).to_equal(1)

        task.reload()
        expect(task.jobs[0].executions[0].status).to_equal(JobExecution.Status.failed)


def test_monitor_job_with_retry2(worker):
    """Test monitoring a job for a task that fails stops after max retries"""

    app = worker.app.app
    with app.app_context():
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
        app.executor = exec_mock

        monitor_queue = app.monitor_queue
        monitor_queue.enqueue(
            Categories.Monitor, task.task_id, job_id, execution.execution_id
        )
        worker.loop_once()

        task.reload()
        expect(task.jobs).to_length(1)

        job = task.jobs[0]
        expect(job.executions).to_length(1)

        execution = job.executions[0]
        expect(execution.image).to_equal("image")
        expect(execution.command).to_equal("command")

        expect(app.redis.zcard(Queue.SCHEDULED_QUEUE_NAME)).to_equal(0)


def test_enqueue_missing1(worker):
    """Test self-healing enqueueing missing monitor jobs"""
    with worker.app.app.app_context():
        app = worker.app.app
        app.redis.flushall()

        for status in [
            JobExecution.Status.enqueued,
            JobExecution.Status.pulling,
            JobExecution.Status.running,
            JobExecution.Status.done,
            JobExecution.Status.failed,
        ]:
            _, job, execution = JobExecutionFixture.new_defaults()
            execution.status = status

            if status == JobExecution.Status.pulling:
                monitor_queue = worker.app.app.monitor_queue
                enqueued_id = monitor_queue.enqueue_in(
                    "1s",
                    Categories.Monitor,
                    job.task.task_id,
                    job.job_id,
                    execution.execution_id,
                )
                job.metadata["enqueued_id"] = enqueued_id

            job.save()

        job_mod.enqueue_missing_monitor_jobs(app)

        res = app.redis.zcard(Queue.SCHEDULED_QUEUE_NAME)
        expect(res).to_equal(2)
