# Standard Library
from datetime import datetime
from json import loads
from unittest.mock import MagicMock
from uuid import uuid4

# 3rd Party
from flask import url_for
from preggy import expect
from rq_scheduler import Scheduler
from tests.fixtures.models import JobExecutionFixture

# Fastlane
from fastlane.models.job import JobExecution

import tests.api.helpers  # NOQA isort:skip pylint:disable=unused-import


def test_get_execution1(client):
    """Test getting tasks with invalid task returns 404"""
    with client.application.app_context():
        task, job, execution = JobExecutionFixture.new_defaults()

        resp = client.get(
            f"/tasks/invalid/jobs/{job.job_id}/executions/{execution.execution_id}"
        )
        msg = f"Task (invalid) or Job ({job.job_id}) not found."
        expect(resp).to_be_an_error_with(
            status=404, msg=msg, operation="get_job_execution"
        )

        resp = client.get(
            f"/tasks/{task.task_id}/jobs/invalid/executions/{execution.execution_id}"
        )
        msg = f"Task ({task.task_id}) or Job (invalid) not found."
        expect(resp).to_be_an_error_with(
            status=404, msg=msg, operation="get_job_execution"
        )

        resp = client.get(f"/tasks/{task.task_id}/jobs/{job.job_id}/executions/invalid")
        msg = f"Job Execution (invalid) not found in job ({job.job_id})."
        expect(resp).to_be_an_error_with(
            status=404, msg=msg, operation="get_job_execution"
        )


def test_get_execution2(client):
    """Test get execution details"""
    with client.application.app_context():
        task, job, execution = JobExecutionFixture.new_defaults()
        resp = client.get(
            f"/tasks/{task.task_id}/jobs/{job.job_id}/executions/{execution.execution_id}"
        )
        expect(resp.status_code).to_equal(200)

        task_url = url_for("task.get_task", task_id=str(task.task_id), _external=True)

        data = loads(resp.data)

        expect(data).to_include("task")
        expect(data["task"]).to_include("id")
        expect(data["task"]).to_include("url")
        expect(data["task"]["id"]).to_equal(task.task_id)
        expect(data["task"]["url"]).to_equal(task_url)

        job_url = url_for(
            "task.get_job",
            task_id=str(task.task_id),
            job_id=str(job.job_id),
            _external=True,
        )
        expect(data).to_include("job")
        expect(data["job"]).to_include("id")
        expect(data["job"]).to_include("url")
        expect(data["job"]["id"]).to_equal(job.job_id)
        expect(data["job"]["url"]).to_equal(job_url)

        expect(data["execution"]["createdAt"]).not_to_be_null()
        del data["execution"]["createdAt"]

        expect(data["execution"]).to_be_like(
            {
                "command": "command",
                "error": None,
                "executionId": execution.execution_id,
                "exitCode": None,
                "finishedAt": None,
                "image": "image",
                "log": None,
                "metadata": execution.metadata,
                "startedAt": None,
                "status": "enqueued",
            }
        )


def test_get_execution_stdout1(client):
    """Test getting job execution stdout"""
    with client.application.app_context():
        task, job, execution = JobExecutionFixture.new_defaults(
            exit_code=0, log="test log", error="some error"
        )

        resp = client.get(
            f"/tasks/{task.task_id}/jobs/{job.job_id}/executions/{execution.execution_id}/stdout/"
        )
        expect(resp.status_code).to_equal(200)
        expect(resp.data).to_equal("test log")


def test_get_execution_stdout2(client):
    """Test getting job execution stdout with invalid data"""
    with client.application.app_context():
        task, job, execution = JobExecutionFixture.new_defaults(
            exit_code=0, log="test log", error="some error"
        )

        resp = client.get(
            f"/tasks/invalid/jobs/{job.job_id}/executions/{execution.execution_id}/stdout/"
        )
        msg = f"Task (invalid) or Job ({job.job_id}) not found."
        expect(resp).to_be_an_error_with(
            status=404, msg=msg, operation="retrieve_execution_details"
        )

        resp = client.get(
            f"/tasks/{task.task_id}/jobs/invalid/executions/{execution.execution_id}/stdout/"
        )
        msg = f"Task ({task.task_id}) or Job (invalid) not found."
        expect(resp).to_be_an_error_with(
            status=404, msg=msg, operation="retrieve_execution_details"
        )

        resp = client.get(
            f"/tasks/{task.task_id}/jobs/{job.job_id}/executions/invalid/stdout/"
        )
        msg = f"No executions found in job with specified arguments."
        expect(resp).to_be_an_error_with(
            status=400, msg=msg, operation="retrieve_execution_details"
        )


def test_get_execution_stderr1(client):
    """Test getting job execution stderr"""
    with client.application.app_context():
        task, job, execution = JobExecutionFixture.new_defaults(
            exit_code=0, log="test log", error="some error"
        )

        resp = client.get(
            f"/tasks/{task.task_id}/jobs/{job.job_id}/executions/{execution.execution_id}/stderr/"
        )
        expect(resp.status_code).to_equal(200)
        expect(resp.data).to_equal("some error")


def test_get_execution_stderr2(client):
    """Test getting job execution stderr with invalid data"""
    with client.application.app_context():
        task, job, execution = JobExecutionFixture.new_defaults(
            exit_code=0, log="test log"
        )

        resp = client.get(
            f"/tasks/invalid/jobs/{job.job_id}/executions/{execution.execution_id}/stderr/"
        )
        msg = f"Task (invalid) or Job ({job.job_id}) not found."
        expect(resp).to_be_an_error_with(
            status=404, msg=msg, operation="retrieve_execution_details"
        )

        resp = client.get(
            f"/tasks/{task.task_id}/jobs/invalid/executions/{execution.execution_id}/stderr/"
        )
        msg = f"Task ({task.task_id}) or Job (invalid) not found."
        expect(resp).to_be_an_error_with(
            status=404, msg=msg, operation="retrieve_execution_details"
        )

        resp = client.get(
            f"/tasks/{task.task_id}/jobs/{job.job_id}/executions/invalid/stderr/"
        )
        msg = "No executions found in job with specified arguments."
        expect(resp).to_be_an_error_with(
            status=400, msg=msg, operation="retrieve_execution_details"
        )


def test_get_execution_logs1(client):
    """Test getting job execution logs"""
    with client.application.app_context():
        task, job, execution = JobExecutionFixture.new_defaults(
            exit_code=0, log="test log", error="some error"
        )

        resp = client.get(
            f"/tasks/{task.task_id}/jobs/{job.job_id}/executions/{execution.execution_id}/logs/"
        )
        expect(resp.status_code).to_equal(200)
        expect(resp.data).to_equal("test log\n-=-\nsome error")


def test_get_execution_logs2(client):
    """Test getting job execution logs with invalid data"""
    with client.application.app_context():
        task, job, execution = JobExecutionFixture.new_defaults(
            exit_code=0, log="test log"
        )

        resp = client.get(
            f"/tasks/invalid/jobs/{job.job_id}/executions/{execution.execution_id}/logs/"
        )

        msg = f"Task (invalid) or Job ({job.job_id}) not found."
        expect(resp).to_be_an_error_with(
            status=404, msg=msg, operation="retrieve_execution_details"
        )

        resp = client.get(
            f"/tasks/{task.task_id}/jobs/invalid/executions/{execution.execution_id}/logs/"
        )
        msg = f"Task ({task.task_id}) or Job (invalid) not found."
        expect(resp).to_be_an_error_with(
            status=404, msg=msg, operation="retrieve_execution_details"
        )

        resp = client.get(
            f"/tasks/{task.task_id}/jobs/{job.job_id}/executions/invalid/logs/"
        )
        msg = "No executions found in job with specified arguments."
        expect(resp).to_be_an_error_with(
            status=400, msg=msg, operation="retrieve_execution_details"
        )


def test_stop_execution1(client):
    with client.application.app_context():

        def test_method():
            pass

        scheduler = Scheduler("jobs", connection=client.application.redis)
        scheduler.enqueue_at(datetime(2020, 1, 1), test_method)

        enqueued_jobs = client.application.redis.zrange(
            b"rq:scheduler:scheduled_jobs", 0, -1
        )

        expect(enqueued_jobs).to_length(1)
        enqueued_job_id = enqueued_jobs[0].decode("utf-8")

        task, job, execution = JobExecutionFixture.new_defaults(
            status=JobExecution.Status.running
        )
        job.metadata["enqueued_id"] = enqueued_job_id
        job.metadata["retries"] = 3
        job.metadata["retry_count"] = 0
        job.save()

        executor_mock = MagicMock()
        client.application.executor = executor_mock

        resp = client.post(
            f"/tasks/{task.task_id}/jobs/{job.job_id}/executions/{execution.execution_id}/stop/"
        )
        expect(resp.status_code).to_equal(200)
        obj = loads(resp.data)
        del obj["execution"]["createdAt"]
        expect(obj).to_be_like(
            {
                "execution": {
                    "command": "command",
                    "error": None,
                    "executionId": execution.execution_id,
                    "exitCode": None,
                    "finishedAt": None,
                    "image": "image",
                    "log": None,
                    "metadata": {
                        "container_id": execution.metadata["container_id"],
                        "docker_host": "host",
                        "docker_port": 1234,
                    },
                    "startedAt": None,
                    "status": "running",
                },
                "job": {
                    "id": job.job_id,
                    "url": f"http://localhost:10000/tasks/{task.task_id}/jobs/{job.job_id}/",
                },
                "task": {
                    "id": task.task_id,
                    "url": f"http://localhost:10000/tasks/{task.task_id}/",
                },
            }
        )

        executor_mock.stop_job.assert_called()
        job.reload()
        expect(job.metadata["retry_count"]).to_equal(4)

        enqueued_jobs = client.application.redis.zrange(
            b"rq:scheduler:scheduled_jobs", 0, -1
        )
        expect(enqueued_jobs).to_length(0)


def test_stop_execution2(client):
    """Test stopping job execution with invalid data"""
    with client.application.app_context():
        task, job, execution = JobExecutionFixture.new_defaults(
            exit_code=0, log="test log"
        )

        resp = client.post(
            f"/tasks/invalid/jobs/{job.job_id}/executions/{execution.execution_id}/stop/"
        )

        msg = f"Task (invalid) or Job ({job.job_id}) not found."
        expect(resp).to_be_an_error_with(
            status=404, msg=msg, operation="stop_job_execution"
        )

        resp = client.post(
            f"/tasks/{task.task_id}/jobs/invalid/executions/{execution.execution_id}/stop/"
        )
        msg = f"Task ({task.task_id}) or Job (invalid) not found."
        expect(resp).to_be_an_error_with(
            status=404, msg=msg, operation="stop_job_execution"
        )

        resp = client.post(
            f"/tasks/{task.task_id}/jobs/{job.job_id}/executions/invalid/stop/"
        )
        msg = f"Job Execution (invalid) not found in Job ({job.job_id})."
        expect(resp).to_be_an_error_with(
            status=404, msg=msg, operation="stop_job_execution"
        )
