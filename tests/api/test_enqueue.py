# Standard Library
from datetime import datetime, timedelta, timezone
from json import dumps, loads
from uuid import uuid4

# 3rd Party
from croniter import croniter
from flask import current_app
from preggy import assertion, create_assertions, expect, utils

# Fastlane
from fastlane.models.job import Job
from fastlane.models.task import Task


@assertion
def to_be_enqueued(topic):
    """Asserts that `topic > expected`."""
    topic = utils.fix_string(topic)

    queue_job_id = utils.fix_string(topic["queueJobId"])
    hash_key = f"rq:job:{queue_job_id}"

    exists = current_app.redis.exists(hash_key)

    if not exists:
        raise AssertionError(
            f"Expected job '{queue_job_id}' to exist but it was not found"
        )

    queue_name = "rq:queue:jobs"
    res = [
        utils.fix_string(job_id)

        for job_id in current_app.redis.lrange(queue_name, -1, 1)
    ]

    for j in res:
        if j == queue_job_id:
            return

    raise AssertionError(
        f"Expected job '{queue_job_id}' to be in the 'jobs' queue, but it was not found("
        f"found jobs: {','.join(res)}."
    )


def has_key(redis, topic, hash_key, expected_key):
    exists = redis.hexists(hash_key, expected_key)

    if not exists:
        available_keys = [
            k for i, k in enumerate(current_app.redis.hgetall(hash_key)) if i % 2 == 0
        ]
        raise AssertionError(
            f"Expected topic('{topic}') to contain '{expected_key}' "
            f"but it was not found (Available keys: {available_keys})"
        )


@assertion
def to_be_enqueued_with_value(topic, expected_key, expected_val=None):
    """Asserts that `job is enqueued with proper value`."""
    topic = utils.fix_string(topic)
    expected_key = utils.fix_string(expected_key)

    queue_job_id = topic["queueJobId"]
    hash_key = f"rq:job:{queue_job_id}"

    if expected_val is None:
        exists = current_app.redis.hexists(hash_key, expected_key)

        if not exists:
            has_key(current_app.redis, topic, hash_key, expected_key)

        return

    if not current_app.redis.hexists(hash_key, expected_key):
        has_key(current_app.redis, topic, hash_key, expected_key)

    curr_val = utils.fix_string(current_app.redis.hget(hash_key, expected_key))

    if curr_val != utils.fix_string(expected_val):
        raise AssertionError(
            f"Expected job to be enqueued with {expected_key}="
            f"'{expected_val}', but it's value was '{curr_val}'."
        )


def test_enqueue1(client):
    """Test enqueue a job works"""

    with client.application.app_context():
        task_id = str(uuid4())
        data = {"image": "ubuntu", "command": "ls"}
        response = client.post(
            f"/tasks/{task_id}", data=dumps(data), follow_redirects=True
        )

        expect(response.status_code).to_equal(200)

        obj = loads(response.data)
        job_id = obj["jobId"]
        expect(job_id).not_to_be_null()
        expect(obj["queueJobId"]).not_to_be_null()

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
            f"fastlane.worker.job.run_job('{obj['taskId']}', '{job_id}', 'ubuntu', 'ls')",
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

        response = client.post(f"/tasks/{task_id}", **options)
        expect(response.status_code).to_equal(200)

        obj = loads(response.data)
        job_id = obj["jobId"]
        expect(job_id).not_to_be_null()
        expect(obj["queueJobId"]).not_to_be_null()

        response = client.post(f"/tasks/{task_id}", **options)
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

    response = client.post(f"/tasks/{task_id}", **options)
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

    response = client.post(f"/tasks/{task_id}", **options)
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

    app = client.application
    app.redis.flushall()

    task_id = str(uuid4())

    data = {"image": "ubuntu", "command": "ls", "cron": "*/10 * * * *"}
    options = dict(
        data=dumps(data),
        headers={"Content-Type": "application/json"},
        follow_redirects=True,
    )

    response = client.post(f"/tasks/{task_id}", **options)
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

    response = client.post(f"/tasks/{task_id}", **options)
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
    app = client.application
    app.redis.flushall()

    task_id = str(uuid4())

    data = {"image": "ubuntu", "command": "ls", "metadata": {"a": 123, "b": 456}}
    options = dict(
        data=dumps(data),
        headers={"Content-Type": "application/json"},
        follow_redirects=True,
    )

    response = client.post(f"/tasks/{task_id}", **options)
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

        response = client.post(f"/tasks/{task_id}", **options)
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

    app = client.application
    app.redis.flushall()

    task_id = str(uuid4())

    options = dict(
        data=None, headers={"Content-Type": "application/json"}, follow_redirects=True
    )

    response = client.post(f"/tasks/{task_id}", **options)
    expect(response.status_code).to_equal(400)
    expect(response.data).to_be_like(
        "Failed to enqueue task because JSON body could not be parsed."
    )


def test_enqueue10(client):
    """Tests that enqueueing without image and command returns 400"""

    app = client.application
    app.redis.flushall()

    task_id = str(uuid4())

    data = {}
    options = dict(
        data=dumps(data),
        headers={"Content-Type": "application/json"},
        follow_redirects=True,
    )

    response = client.post(f"/tasks/{task_id}", **options)
    expect(response.status_code).to_equal(400)
    expect(response.data).to_be_like("image and command must be filled in the request.")


def test_enqueue11(client):
    """
    Tests that enqueueing with multiple scheduling options:
    startAt, startIn or cron returns 400
    """

    app = client.application
    app.redis.flushall()

    task_id = str(uuid4())

    time = int(datetime.now(tz=timezone.utc).timestamp())

    data = {"image": "ubuntu", "command": "ls", "startAt": time, "cron": "* * * * *"}
    options = dict(
        data=dumps(data),
        headers={"Content-Type": "application/json"},
        follow_redirects=True,
    )

    response = client.post(f"/tasks/{task_id}", **options)
    expect(response.status_code).to_equal(400)
    expect(response.data).to_be_like(
        "Only ONE of 'startAt', 'startIn' and 'cron' should be in the request."
    )


def test_enqueue12(client):
    """Test enqueue a job works with PUT"""
    task_id = str(uuid4())
    job_id = str(uuid4())
    data = {"image": "ubuntu", "command": "ls"}
    response = client.put(
        f"/tasks/{task_id}/jobs/{job_id}", data=dumps(data), follow_redirects=True
    )

    expect(response.status_code).to_equal(200)

    obj = loads(response.data)
    expect(obj).not_to_be_null()
    new_job_id = obj["jobId"]
    expect(new_job_id).to_equal(job_id)
    expect(obj["queueJobId"]).not_to_be_null()

    # app = client.application
    # task = Task.get_by_task_id(obj["taskId"])

    # with app.app_context():
    # expect(obj["taskUrl"]).to_equal(task.get_url())

    # queue_job_id = obj["queueJobId"]
    # hash_key = f"rq:job:{queue_job_id}"

    # res = app.redis.exists(hash_key)
    # expect(res).to_be_true()

    # res = app.redis.hget(hash_key, "status")
    # expect(res).to_equal("queued")

    # res = app.redis.hexists(hash_key, "created_at")
    # expect(res).to_be_true()

    # res = app.redis.hexists(hash_key, "enqueued_at")
    # expect(res).to_be_true()

    # res = app.redis.hexists(hash_key, "data")
    # expect(res).to_be_true()

    # res = app.redis.hget(hash_key, "origin")
    # expect(res).to_equal("jobs")

    # res = app.redis.hget(hash_key, "description")
    # expect(res).to_equal(
    # f"fastlane.worker.job.run_job('{obj['taskId']}', '{job_id}', 'ubuntu', 'ls')"
    # )

    # res = app.redis.hget(hash_key, "timeout")
    # expect(res).to_equal("-1")

    # expect(task).not_to_be_null()
    # expect(task.jobs).not_to_be_empty()

    # j = task.jobs[0]
    # expect(str(j.id)).to_equal(job_id)

    # queue_name = "rq:queue:jobs"
    # res = app.redis.llen(queue_name)
    # expect(res).to_equal(1)

    # res = app.redis.lpop(queue_name)
    # expect(res).to_equal(queue_job_id)

    # with app.app_context():
    # count = Task.objects.count()
    # expect(count).to_equal(1)
