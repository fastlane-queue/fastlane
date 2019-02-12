# Standard Library
from datetime import datetime, timedelta, timezone
from json import dumps, loads
from uuid import uuid4

# 3rd Party
import pytest
from croniter import croniter
from preggy import expect

# Fastlane
from fastlane.models import Job, Task

import tests.unit.api.helpers  # NOQA isort:skip pylint:disable=unused-import


def test_enqueue1(client):
    """Test enqueue a job works"""

    with client.application.app_context():
        task_id = str(uuid4())
        data = {"image": "ubuntu", "command": "ls"}
        response = client.post(
            f"/tasks/{task_id}/", data=dumps(data), follow_redirects=True
        )

        expect(response.status_code).to_equal(200)
        obj = loads(response.data)

        expect(obj["taskUrl"]).to_equal(f"http://localhost:10000/tasks/{task_id}/")

        job_id = obj["jobId"]
        expect(job_id).not_to_be_null()

        expect(obj["jobUrl"]).to_equal(
            f"http://localhost:10000/tasks/{task_id}/jobs/{job_id}/"
        )

        expect(obj["queueJobId"]).not_to_be_null()

        expect(obj["executionId"]).not_to_be_null()
        execution_id = obj["executionId"]

        expect(obj["executionUrl"]).to_equal(
            f"http://localhost:10000/tasks/{task_id}/jobs/{job_id}/executions/{execution_id}/"
        )

        task = Task.get_by_task_id(obj["taskId"])
        expect(task).not_to_be_null()
        expect(task.jobs).not_to_be_empty()

        j = task.jobs[0]
        job = Job.objects(id=j.id).first()
        expect(str(job.job_id)).to_equal(job_id)

        expect(obj["taskUrl"]).to_equal(task.get_url())
        expect(obj).to_be_enqueued()
        expect(obj).to_be_enqueued_with_value("status", "queued")

        expect(obj).to_be_enqueued_with_value("created_at")
        expect(obj).to_be_enqueued_with_value("enqueued_at")
        expect(obj).to_be_enqueued_with_value("data")
        expect(obj).to_be_enqueued_with_value("origin", "jobs")
        expect(obj).to_be_enqueued_with_value(
            "description",
            f"fastlane.worker.job.run_job('{obj['taskId']}', '{job_id}', '{execution_id}', 'ubuntu', 'ls')",
        )
        expect(obj).to_be_enqueued_with_value("timeout", "-1")

        count = Task.objects.count()
        expect(count).to_equal(1)


def test_enqueue2(client):
    """Test enqueue a job with the same task does not create a new task"""

    with client.application.app_context():
        task_id = str(uuid4())

        data = {"image": "ubuntu", "command": "ls"}

        options = dict(
            data=dumps(data),
            headers={"Content-Type": "application/json"},
            follow_redirects=True,
        )

        response = client.post(f"/tasks/{task_id}/", **options)
        expect(response.status_code).to_equal(200)

        obj = loads(response.data)
        job_id = obj["jobId"]
        expect(job_id).not_to_be_null()
        expect(obj["queueJobId"]).not_to_be_null()

        response = client.post(f"/tasks/{task_id}/", **options)
        expect(response.status_code).to_equal(200)
        obj = loads(response.data)
        job_id = obj["jobId"]
        expect(job_id).not_to_be_null()
        expect(obj["queueJobId"]).not_to_be_null()

        expect(obj).to_be_enqueued()

        task = Task.get_by_task_id(obj["taskId"])
        expect(task).not_to_be_null()
        expect(task.jobs).not_to_be_empty()

        count = Task.objects.count()
        expect(count).to_equal(1)


def test_enqueue3(client):
    """Test enqueue a job at a future specific time"""

    with client.application.app_context():
        app = client.application
        app.redis.flushall()

        task_id = str(uuid4())

        time = int(datetime.now(tz=timezone.utc).timestamp())

        data = {"image": "ubuntu", "command": "ls", "startAt": time}
        options = dict(
            data=dumps(data),
            headers={"Content-Type": "application/json"},
            follow_redirects=True,
        )

        response = client.post(f"/tasks/{task_id}/", **options)
        expect(response.status_code).to_equal(200)
        obj = loads(response.data)
        job_id = obj["jobId"]
        expect(job_id).not_to_be_null()
        expect(obj["queueJobId"]).not_to_be_null()

        res = app.redis.zrange(b"rq:scheduler:scheduled_jobs", 0, -1)
        expect(res).to_length(1)

        res = app.redis.zscore("rq:scheduler:scheduled_jobs", res[0])
        expect(res).to_equal(time)


def test_enqueue4(client):
    """Test enqueue a job in an hour"""

    with client.application.app_context():
        cases = (
            ("48h", timedelta(hours=48)),
            ("1h", timedelta(hours=1)),
            ("5m", timedelta(minutes=5)),
            ("30s", timedelta(seconds=30)),
        )

        for (start_in, delta) in cases:
            enqueue_in(client, start_in, delta)


def enqueue_in(client, start_in, delta):
    app = client.application
    app.redis.flushall()

    task_id = str(uuid4())

    data = {"image": "ubuntu", "command": "ls", "startIn": start_in}
    options = dict(
        data=dumps(data),
        headers={"Content-Type": "application/json"},
        follow_redirects=True,
    )

    response = client.post(f"/tasks/{task_id}/", **options)
    expect(response.status_code).to_equal(200)
    obj = loads(response.data)
    job_id = obj["jobId"]
    expect(job_id).not_to_be_null()
    expect(obj["queueJobId"]).not_to_be_null()

    # res = app.redis.keys()
    res = app.redis.zrange(b"rq:scheduler:scheduled_jobs", 0, -1)
    expect(res).to_length(1)

    time = int((datetime.now(tz=timezone.utc) + delta).timestamp())
    res = app.redis.zscore("rq:scheduler:scheduled_jobs", res[0])
    expect(res).to_be_greater_than(time - 2)
    expect(res).to_be_lesser_than(time + 2)


def test_enqueue5(client):
    """Test enqueue a job using cron"""

    with client.application.app_context():
        app = client.application
        app.redis.flushall()

        task_id = str(uuid4())

        data = {"image": "ubuntu", "command": "ls", "cron": "*/10 * * * *"}
        options = dict(
            data=dumps(data),
            headers={"Content-Type": "application/json"},
            follow_redirects=True,
        )

        response = client.post(f"/tasks/{task_id}/", **options)
        expect(response.status_code).to_equal(200)
        obj = loads(response.data)
        job_id = obj["jobId"]
        expect(job_id).not_to_be_null()
        expect(obj["queueJobId"]).not_to_be_null()

        res = app.redis.zrange(b"rq:scheduler:scheduled_jobs", 0, -1)
        expect(res).to_length(1)

        cron = croniter("*/10 * * * *", datetime.now())
        res = app.redis.zscore("rq:scheduler:scheduled_jobs", res[0])
        expected = cron.get_next(datetime)
        expect(res).to_equal(expected.timestamp())


def test_enqueue6(client):
    """Test enqueue with webhooks"""

    with client.application.app_context():
        app = client.application
        app.redis.flushall()

        task_id = str(uuid4())

        data = {
            "image": "ubuntu",
            "command": "ls",
            "webhooks": {
                "succeeds": [{"method": "GET", "url": "http://some.test.url"}],
                "fails": [{"method": "GET", "url": "http://some.test.url"}],
                "finishes": [{"method": "POST", "url": "http://some.test.url"}],
            },
        }
        options = dict(
            data=dumps(data),
            headers={"Content-Type": "application/json"},
            follow_redirects=True,
        )

        response = client.post(f"/tasks/{task_id}/", **options)
        expect(response.status_code).to_equal(200)
        obj = loads(response.data)
        job_id = obj["jobId"]
        expect(job_id).not_to_be_null()
        expect(obj["queueJobId"]).not_to_be_null()

        j = Job.get_by_id(task_id, job_id)
        expect(j).not_to_be_null()
        expect(j.metadata).to_include("webhooks")

        webhooks = j.metadata["webhooks"]
        expect(webhooks).to_be_like(data["webhooks"])


def test_enqueue7(client):
    """Test enqueue with metadata"""

    with client.application.app_context():
        app = client.application
        app.redis.flushall()

        task_id = str(uuid4())

        data = {"image": "ubuntu", "command": "ls", "metadata": {"a": 123, "b": 456}}
        options = dict(
            data=dumps(data),
            headers={"Content-Type": "application/json"},
            follow_redirects=True,
        )

        response = client.post(f"/tasks/{task_id}/", **options)
        expect(response.status_code).to_equal(200)
        obj = loads(response.data)
        job_id = obj["jobId"]
        expect(job_id).not_to_be_null()
        expect(obj["queueJobId"]).not_to_be_null()

        j = Job.get_by_id(task_id, job_id)
        expect(j.metadata).to_include("custom")

        metadata = j.metadata["custom"]
        expect(metadata).to_be_like(data["metadata"])


def test_enqueue8(client):
    """Test enqueue ignore metadata if not dict"""

    with client.application.app_context():
        cases = ("qwe", 123, ["as"], [{"a": 123}])

        def enqueue(client, input_data):
            app = client.application
            app.redis.flushall()

            task_id = str(uuid4())

            data = {"image": "ubuntu", "command": "ls", "metadata": input_data}
            options = dict(
                data=dumps(data),
                headers={"Content-Type": "application/json"},
                follow_redirects=True,
            )

            response = client.post(f"/tasks/{task_id}/", **options)
            expect(response.status_code).to_equal(200)
            obj = loads(response.data)
            job_id = obj["jobId"]
            expect(job_id).not_to_be_null()
            expect(obj["queueJobId"]).not_to_be_null()

            j = Job.get_by_id(task_id, job_id)
            expect(j.metadata).not_to_include("custom")

        for input_data in cases:
            enqueue(client, input_data)


def test_enqueue9(client):
    """Tests that enqueueing with invalid or empty body returns 400"""

    with client.application.app_context():
        app = client.application
        app.redis.flushall()

        task_id = str(uuid4())

        options = dict(
            data=None,
            headers={"Content-Type": "application/json"},
            follow_redirects=True,
        )

        response = client.post(f"/tasks/{task_id}/", **options)
        expect(response.status_code).to_equal(400)
        expect(response.data).to_be_like(
            "Failed to enqueue task because JSON body could not be parsed."
        )


def test_enqueue10(client):
    """Tests that enqueueing without image and command returns 400"""

    with client.application.app_context():
        app = client.application
        app.redis.flushall()

        task_id = str(uuid4())

        data = {}
        options = dict(
            data=dumps(data),
            headers={"Content-Type": "application/json"},
            follow_redirects=True,
        )

        response = client.post(f"/tasks/{task_id}/", **options)
        expect(response.status_code).to_equal(400)
        expect(response.data).to_be_like(
            "image and command must be filled in the request."
        )


def test_enqueue11(client):
    """
    Tests that enqueueing with multiple scheduling options:
    startAt, startIn or cron returns 400
    """

    with client.application.app_context():
        app = client.application
        app.redis.flushall()

        task_id = str(uuid4())

        time = int(datetime.now(tz=timezone.utc).timestamp())

        data = {
            "image": "ubuntu",
            "command": "ls",
            "startAt": time,
            "cron": "* * * * *",
        }
        options = dict(
            data=dumps(data),
            headers={"Content-Type": "application/json"},
            follow_redirects=True,
        )

        response = client.post(f"/tasks/{task_id}/", **options)
        expect(response.status_code).to_equal(400)
        expect(response.data).to_be_like(
            "Only ONE of 'startAt', 'startIn' and 'cron' should be in the request."
        )


def test_enqueue12(client):
    """Test enqueue a job works with PUT"""

    with client.application.app_context():
        task_id = str(uuid4())
        job_id = str(uuid4())
        data = {"image": "ubuntu", "command": "ls"}
        response = client.put(
            f"/tasks/{task_id}/jobs/{job_id}/", data=dumps(data), follow_redirects=True
        )

        expect(response.status_code).to_equal(200)

        obj = loads(response.data)
        expect(obj).not_to_be_null()
        new_job_id = obj["jobId"]
        expect(new_job_id).to_equal(job_id)
        expect(obj["queueJobId"]).not_to_be_null()

        expect(obj["executionId"]).not_to_be_null()
        execution_id = obj["executionId"]

        task = Task.get_by_task_id(obj["taskId"])
        expect(task).not_to_be_null()
        expect(task.jobs).not_to_be_empty()

        j = task.jobs[0]
        job = Job.objects(id=j.id).first()
        expect(str(job.job_id)).to_equal(job_id)

        expect(obj["taskUrl"]).to_equal(task.get_url())
        expect(obj).to_be_enqueued()
        expect(obj).to_be_enqueued_with_value("status", "queued")

        expect(obj).to_be_enqueued_with_value("created_at")
        expect(obj).to_be_enqueued_with_value("enqueued_at")
        expect(obj).to_be_enqueued_with_value("data")
        expect(obj).to_be_enqueued_with_value("origin", "jobs")
        expect(obj).to_be_enqueued_with_value(
            "description",
            (
                f"fastlane.worker.job.run_job('{obj['taskId']}', '{job_id}', "
                f"'{execution_id}', 'ubuntu', 'ls')"
            ),
        )
        expect(obj).to_be_enqueued_with_value("timeout", "-1")

        count = Task.objects.count()
        expect(count).to_equal(1)


def test_enqueue13(client):
    """Tests enqueue stores IP Address for request using X-Real-IP."""
    pytest.skip("Not implemented")


def test_enqueue14(client):
    """Tests enqueue stores IP Address for request using X-Forwarded-For first value as fallback."""
    pytest.skip("Not implemented")


def test_enqueue15(client):
    """Tests enqueue stores IP Address for request using request address as fallback."""
    pytest.skip("Not implemented")


def test_enqueue16(client):
    """Tests POST enqueue works when used without last slash."""
    with client.application.app_context():
        task_id = str(uuid4())
        data = {"image": "ubuntu", "command": "ls"}
        response = client.post(
            f"/tasks/{task_id}", data=dumps(data), follow_redirects=False
        )
        expect(response.status_code).to_equal(200)


def test_enqueue17(client):
    """Tests PUT enqueue works when accessed without last slash."""
    with client.application.app_context():
        task_id = str(uuid4())
        job_id = str(uuid4())
        data = {"image": "ubuntu", "command": "ls"}
        response = client.put(
            f"/tasks/{task_id}/jobs/{job_id}", data=dumps(data), follow_redirects=False
        )

        expect(response.status_code).to_equal(200)
