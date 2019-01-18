# Standard Library
from json import loads

# 3rd Party
from flask import url_for
from preggy import expect
from tests.fixtures.models import JobExecutionFixture

# Fastlane
from fastlane.models.task import Task


def test_get_execution1(client):
    """Test getting tasks with invalid task returns 404"""
    with client.application.app_context():
        task = Task.create_task("my-task-1")
        job = task.create_job()
        execution = job.create_execution("image", "command")

        resp = client.get(
            f"/tasks/invalid/jobs/{job.job_id}/executions/{execution.execution_id}"
        )
        expect(resp.status_code).to_equal(404)
        expect(resp.data).to_equal(f"Task (invalid) or Job ({job.job_id}) not found.")

        resp = client.get(
            f"/tasks/{task.task_id}/jobs/invalid/executions/{execution.execution_id}"
        )
        expect(resp.status_code).to_equal(404)
        expect(resp.data).to_equal(f"Task ({task.task_id}) or Job (invalid) not found.")

        resp = client.get(f"/tasks/{task.task_id}/jobs/{job.job_id}/executions/invalid")
        expect(resp.status_code).to_equal(404)
        expect(resp.data).to_equal(
            f"Job Execution (invalid) not found in job ({job.job_id})."
        )


def test_get_execution2(client):
    """Test getting tasks"""
    with client.application.app_context():
        task = Task.create_task("my-task-1")
        job = task.create_job()
        execution = job.create_execution("image", "command")

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
                "metadata": {},
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
        expect(resp.status_code).to_equal(404)
        expect(resp.data).to_equal(f"Task (invalid) or Job ({job.job_id}) not found.")

        resp = client.get(
            f"/tasks/{task.task_id}/jobs/invalid/executions/{execution.execution_id}/stdout/"
        )
        expect(resp.status_code).to_equal(404)
        expect(resp.data).to_equal(f"Task ({task.task_id}) or Job (invalid) not found.")

        resp = client.get(
            f"/tasks/{task.task_id}/jobs/{job.job_id}/executions/invalid/stdout/"
        )
        expect(resp.status_code).to_equal(404)
        expect(resp.data).to_equal(
            "No executions found in job with specified arguments."
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
        expect(resp.status_code).to_equal(404)
        expect(resp.data).to_equal(f"Task (invalid) or Job ({job.job_id}) not found.")

        resp = client.get(
            f"/tasks/{task.task_id}/jobs/invalid/executions/{execution.execution_id}/stderr/"
        )
        expect(resp.status_code).to_equal(404)
        expect(resp.data).to_equal(f"Task ({task.task_id}) or Job (invalid) not found.")

        resp = client.get(
            f"/tasks/{task.task_id}/jobs/{job.job_id}/executions/invalid/stderr/"
        )
        expect(resp.status_code).to_equal(404)
        expect(resp.data).to_equal(
            "No executions found in job with specified arguments."
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
        expect(resp.status_code).to_equal(404)
        expect(resp.data).to_equal(f"Task (invalid) or Job ({job.job_id}) not found.")

        resp = client.get(
            f"/tasks/{task.task_id}/jobs/invalid/executions/{execution.execution_id}/logs/"
        )
        expect(resp.status_code).to_equal(404)
        expect(resp.data).to_equal(f"Task ({task.task_id}) or Job (invalid) not found.")

        resp = client.get(
            f"/tasks/{task.task_id}/jobs/{job.job_id}/executions/invalid/logs/"
        )
        expect(resp.status_code).to_equal(404)
        expect(resp.data).to_equal(
            "No executions found in job with specified arguments."
        )