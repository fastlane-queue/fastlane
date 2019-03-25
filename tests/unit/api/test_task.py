# Standard Library
from json import loads
from uuid import uuid4

# 3rd Party
import pytest
from preggy import expect
from tests.fixtures.models import JobExecutionFixture

# Fastlane
from fastlane.models.job_execution import JobExecution
from fastlane.models.task import Task
from fastlane.utils import from_unix, unix_now


def test_get_tasks(client):
    """Test getting tasks"""
    Task.create_task("my-task-1")
    Task.create_task("my-task-2")
    Task.create_task("my-task-3")

    resp = client.get("/tasks/")
    expect(resp.status_code).to_equal(200)

    data = loads(resp.data)
    expect(data["items"]).to_length(3)
    expect(data["total"]).to_equal(3)
    expect(data["page"]).to_equal(1)
    expect(data["pages"]).to_equal(1)
    expect(data["perPage"]).to_equal(3)
    expect(data["hasNext"]).to_be_false()
    expect(data["hasPrev"]).to_be_false()


def test_get_tasks2(client):
    """Test getting tasks returns CORS headers"""
    resp = client.get("/tasks/")
    expect(resp.status_code).to_equal(200)
    headers = dict(resp.headers)
    expect(headers).to_include("Access-Control-Allow-Origin")
    expect(headers["Access-Control-Allow-Origin"]).to_equal("*")


def test_get_tasks3(client):
    """Test getting tasks returns CORS headers with custom origin"""
    client.application.config["CORS_ORIGINS"] = "domain.com"
    resp = client.get("/tasks/")
    expect(resp.status_code).to_equal(200)
    headers = dict(resp.headers)
    expect(headers).to_include("Access-Control-Allow-Origin")
    expect(headers["Access-Control-Allow-Origin"]).to_equal("*")


def test_get_tasks_data(client):
    """Test getting tasks resource data"""
    task = Task.create_task("my-task")

    resp = client.get("/tasks/")

    data = loads(resp.data)
    task_data = data["items"][0]

    with client.application.app_context():
        expect(task_data.keys()).to_equal(task.to_dict().keys())


def test_get_tasks_pagination(client):
    """Test getting tasks pagination"""
    Task.create_task("my-task-1")
    Task.create_task("my-task-2")
    Task.create_task("my-task-3")
    Task.create_task("my-task-4")

    app = client.application
    server_name = app.config["SERVER_NAME"]

    resp = client.get("/tasks/?page=2")

    data = loads(resp.data)
    expect(data["total"]).to_equal(4)
    expect(data["page"]).to_equal(2)
    expect(data["hasNext"]).to_be_false()
    expect(data["hasPrev"]).to_be_true()
    expect(data["prevUrl"]).to_equal(f"http://{server_name}/tasks/?page=1")
    expect(data["nextUrl"]).to_be_null()


def test_get_tasks_pagination2(client):
    """
    Test getting tasks pagination should respond 400 when page is invalid
    """
    resp1 = client.get("/tasks/?page=asdasdas")
    expect(resp1.status_code).to_equal(400)

    resp2 = client.get("/tasks/?page=1019021")
    expect(resp2.status_code).to_equal(404)

    resp3 = client.get("/tasks/?page=0")
    expect(resp3.status_code).to_equal(400)

    resp4 = client.get("/tasks/?page=-1")
    expect(resp4.status_code).to_equal(400)


def test_get_task_details(client):
    """Test getting tasks"""
    task_id = str(uuid4())
    job_id = str(uuid4())
    task = Task.create_task(task_id)
    task.create_or_update_job(job_id, "ubuntu", "command")

    resp = client.get(f"/tasks/{task_id}/")
    expect(resp.status_code).to_equal(200)

    data = loads(resp.data)
    expect(data).to_include("jobs")
    expect(data["jobs"]).to_length(1)

    job_data = data["jobs"][0]
    expect(job_data).to_include("id")
    expect(job_data["id"]).to_equal(job_id)
    expect(job_data["url"]).to_equal(
        f"http://localhost:10000/tasks/{task_id}/jobs/{job_id}/"
    )


def test_search_tasks1(client):
    """Tests search task by task_id."""

    task_id = f"task-search-{str(uuid4())}"
    Task.create_task(task_id)
    Task.create_task(str(uuid4()))
    Task.create_task(str(uuid4()))

    resp = client.get("/search/?query=search")
    expect(resp.status_code).to_equal(200)

    data = loads(resp.data)
    expect(data["items"]).to_length(1)


def test_search_tasks2(client):
    """
    Test search tasks pagination should respond error when page is invalid
    """
    resp1 = client.get("/search/?query=qwe&page=asdasdas")
    expect(resp1.status_code).to_equal(400)

    resp2 = client.get("/search/?query=qwe&page=1019021")
    expect(resp2.status_code).to_equal(404)

    resp3 = client.get("/search/?query=qwe&page=0")
    expect(resp3.status_code).to_equal(400)

    resp4 = client.get("/search/?query=qwe&page=-1")
    expect(resp4.status_code).to_equal(400)


def test_job_details1(client):
    """Tests get job details returns proper details and last 20 execs by last updated at."""

    task, job, execution = JobExecutionFixture.new_defaults()
    now = unix_now()

    for i in range(30):
        ex = job.create_execution("ubuntu", "ls")
        ex.created_at = from_unix(now + (i * 10))
        ex.save()

    resp1 = client.get(f"/tasks/{task.task_id}/jobs/{job.job_id}/")
    expect(resp1.status_code).to_equal(200)
    obj = loads(resp1.data)

    expect(obj["job"]["executions"]).to_length(20)
    executions = obj["job"]["executions"]

    for i in range(20):
        ex = executions[i]
        dt = from_unix(now + (29 - i) * 10)
        expect(ex["createdAt"]).to_equal(dt.isoformat())


def test_job_stdout1(client):
    """Tests get job stdout returns log for last execution."""

    task, job, execution = JobExecutionFixture.new_defaults()
    execution.log = "test log"
    execution.status = JobExecution.Status.done
    execution.save()

    resp1 = client.get(f"/tasks/{task.task_id}/jobs/{job.job_id}/stdout/")
    expect(resp1.status_code).to_equal(200)
    expect(resp1.data).to_equal("test log")


def test_job_stdout2(client):
    """Tests get job stdout fails if invalid input."""

    task, _, _ = JobExecutionFixture.new_defaults()
    resp1 = client.get(f"/tasks/{task.task_id}/jobs/invalid-id/stdout/")
    expect(resp1.status_code).to_equal(404)
    obj = loads(resp1.data)
    expect(obj["error"]).to_equal(
        f"Job (invalid-id) with Task ({task.task_id}) not found."
    )
    expect(obj["operation"]).to_equal("stdout")


def test_job_stderr1(client):
    """Tests get job stderr returns log for last execution."""

    task, job, execution = JobExecutionFixture.new_defaults()
    execution.error = "test error"
    execution.status = JobExecution.Status.done
    execution.save()

    resp1 = client.get(f"/tasks/{task.task_id}/jobs/{job.job_id}/stderr/")
    expect(resp1.status_code).to_equal(200)
    expect(resp1.data).to_equal("test error")


def test_job_stderr2(client):
    """Tests get job stderr fails if invalid input."""

    task, job, execution = JobExecutionFixture.new_defaults()

    resp1 = client.get(f"/tasks/{task.task_id}/jobs/invalid-id/stderr/")
    expect(resp1.status_code).to_equal(404)
    obj = loads(resp1.data)
    expect(obj["error"]).to_equal(
        f"Job (invalid-id) with Task ({task.task_id}) not found."
    )
    expect(obj["operation"]).to_equal("stderr")


def test_job_logs1(client):
    """Tests get job logs returns log for last execution."""

    task, job, execution = JobExecutionFixture.new_defaults()
    execution.log = "test log"
    execution.error = "test error"
    execution.status = JobExecution.Status.done
    execution.save()

    resp1 = client.get(f"/tasks/{task.task_id}/jobs/{job.job_id}/logs/")
    expect(resp1.status_code).to_equal(200)
    expect(resp1.data).to_equal("test log\n-=-\ntest error")


def test_job_logs2(client):
    """Tests get job logs fails if invalid input."""

    task, job, execution = JobExecutionFixture.new_defaults()

    resp1 = client.get(f"/tasks/{task.task_id}/jobs/invalid-id/logs/")
    expect(resp1.status_code).to_equal(404)
    obj = loads(resp1.data)
    expect(obj["error"]).to_equal(
        f"Job (invalid-id) with Task ({task.task_id}) not found."
    )
    expect(obj["operation"]).to_equal("logs")


def test_stop_container1(client):
    """Tests that stopping a running container actually stops the container."""
    pytest.skip("Not implemented")


def test_stop_container2(client):
    """Tests that stopping a scheduled job kills the scheduling."""
    pytest.skip("Not implemented")


def test_stop_container3(client):
    """Tests that stopping a CRON job kills the scheduling."""
    pytest.skip("Not implemented")


def test_stop_container4(client):
    """Tests that stopping without an end slash fails with 404."""
    pytest.skip("Not implemented")


def test_stop_container5(client):
    """Tests that stopping a scheduled job with no executions actually kills the scheduled job."""
    pytest.skip("Not implemented")
