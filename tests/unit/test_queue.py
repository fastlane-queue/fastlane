# Standard Library
from datetime import datetime

# 3rd Party
from preggy import expect

# Fastlane
from fastlane.queue import Categories, Message, Queue
from fastlane.utils import get_next_cron_timestamp, to_unix


def assert_queue_message(queue, expected_size, message_id):
    redis = queue.redis

    expect(redis.llen(queue.queue_name)).to_equal(expected_size)

    if expected_size > 0:
        retrieved_id = redis.lpop(queue.queue_name).decode("utf-8")
        expect(retrieved_id).to_equal(message_id)

        message_str = redis.get(Queue.get_message_name(message_id))
        expect(message_str).not_to_be_null()

        message = Message.deserialize(message_str)
        expect(message.id).to_equal(message_id)
    else:
        message_exists = redis.exists(Queue.get_message_name(message_id))
        expect(message_exists).to_be_false()


def test_queueing(client):
    """Test enqueueing a new message"""

    queue = client.application.jobs_queue
    expect(queue).not_to_be_null()

    enqueued_id = queue.enqueue(Categories.Job)
    assert_queue_message(queue, 1, enqueued_id)


def test_dequeue1(client):
    """Test dequeue a job"""

    queue = client.application.jobs_queue
    expect(queue).not_to_be_null()

    for test_case in [{}, dict(blocking=True, timeout=1)]:
        enqueued_id = queue.enqueue(Categories.Job, "something", other="öther")

        redis = client.application.redis
        expect(redis.llen(queue.queue_name)).to_equal(1)

        job = queue.dequeue(**test_case)
        expect(job.id).to_equal(enqueued_id)
        expect(job.category).to_equal(Categories.Job)
        expect(job.args).to_length(1)
        expect(job.args[0]).to_equal("something")
        expect(job.kwargs).to_include("other")
        expect(job.kwargs["other"]).to_equal("öther")

        assert_queue_message(queue, 0, enqueued_id)


def test_dequeue2(client):
    """Test dequeue works when no jobs available"""

    queue = client.application.jobs_queue
    result = queue.dequeue()
    expect(result).to_be_null()


def test_dequeue3(client):
    """Test blocking dequeue works when no jobs available"""

    queue = client.application.jobs_queue

    redis = client.application.redis
    expect(redis.llen(queue.queue_name)).to_equal(0)

    result = queue.dequeue(blocking=True, timeout=1)
    expect(result).to_be_null()


def test_schedule1(client):
    """Test Scheduling a job for UTC unix timestamp"""

    queue = client.application.jobs_queue

    timestamp = to_unix(datetime.utcnow())

    enqueued_id = queue.enqueue_at(
        timestamp, Categories.Monitor, "something", other="öther"
    )

    redis = client.application.redis
    expect(redis.llen(queue.queue_name)).to_equal(0)

    expect(redis.zcard(Queue.SCHEDULED_QUEUE_NAME)).to_equal(1)

    items = redis.zrange(Queue.SCHEDULED_QUEUE_NAME, 0, -1, withscores=True)
    expect(items).to_length(1)

    message_id, actual_ts = items[0]
    expect(actual_ts).to_equal(timestamp)
    expect(message_id).to_equal(enqueued_id)

    message_key = queue.get_message_name(enqueued_id)
    expect(redis.exists(message_key)).to_be_true()

    data = redis.get(message_key)

    job = Message.deserialize(data)

    expect(job.id).to_equal(enqueued_id)
    expect(job.category).to_equal(Categories.Monitor)
    expect(job.args).to_length(1)
    expect(job.args[0]).to_equal("something")
    expect(job.kwargs).to_include("other")
    expect(job.kwargs["other"]).to_equal("öther")


def test_schedule2(client):
    """Test Scheduling a job in a few seconds"""

    queue = client.application.jobs_queue

    timestamp = to_unix(datetime.utcnow()) + 5

    enqueued_id = queue.enqueue_in("5s", Categories.Monitor, "something", other="öther")

    redis = client.application.redis
    expect(redis.llen(queue.queue_name)).to_equal(0)

    expect(redis.zcard(Queue.SCHEDULED_QUEUE_NAME)).to_equal(1)

    items = redis.zrange(Queue.SCHEDULED_QUEUE_NAME, 0, -1, withscores=True)
    expect(items).to_length(1)

    message_id, actual_ts = items[0]
    expect(actual_ts).to_equal(timestamp)
    expect(message_id).to_equal(enqueued_id)

    message_key = queue.get_message_name(enqueued_id)
    expect(redis.exists(message_key)).to_be_true()

    data = redis.get(message_key)

    job = Message.deserialize(data)

    expect(job.id).to_equal(enqueued_id)
    expect(job.category).to_equal(Categories.Monitor)
    expect(job.args).to_length(1)
    expect(job.args[0]).to_equal("something")
    expect(job.kwargs).to_include("other")
    expect(job.kwargs["other"]).to_equal("öther")


def test_schedule3(client):
    """Test Scheduling a job with cron"""

    queue = client.application.jobs_queue

    cron_str = "* * * * *"
    timestamp = to_unix(get_next_cron_timestamp(cron_str))

    enqueued_id = queue.enqueue_cron(
        cron_str, Categories.Monitor, "something", other="öther"
    )

    redis = client.application.redis
    expect(redis.llen(queue.queue_name)).to_equal(0)

    expect(redis.zcard(Queue.SCHEDULED_QUEUE_NAME)).to_equal(1)

    items = redis.zrange(Queue.SCHEDULED_QUEUE_NAME, 0, -1, withscores=True)
    expect(items).to_length(1)

    message_id, actual_ts = items[0]
    expect(actual_ts).to_equal(timestamp)
    expect(message_id).to_equal(enqueued_id)

    message_key = queue.get_message_name(enqueued_id)
    expect(redis.exists(message_key)).to_be_true()

    data = redis.get(message_key)

    job = Message.deserialize(data)
    job = Message.deserialize(data)

    expect(job.id).to_equal(enqueued_id)
    expect(job.category).to_equal(Categories.Monitor)
    expect(job.args).to_length(1)
    expect(job.args[0]).to_equal("something")
    expect(job.kwargs).to_include("other")
    expect(job.kwargs["other"]).to_equal("öther")


def test_move_jobs(client):
    """Test moving jobs from scheduled to enqueued"""

    redis = client.application.redis
    jobs_queue = client.application.jobs_queue
    enqueued_ids = []

    for offset in range(-5, 6):
        if offset == 0:
            continue
        timestamp = to_unix(datetime.utcnow()) + offset * 2
        enqueued_ids.append(
            jobs_queue.enqueue_at(
                timestamp,
                Categories.Notify,
                f"something {offset}",
                other=f"öther {offset}",
            )
        )

        expect(redis.exists(Queue.get_message_name(enqueued_ids[-1]))).to_be_true()

    expect(redis.zcard(Queue.SCHEDULED_QUEUE_NAME)).to_equal(10)

    moved = client.application.queue_group.move_jobs()
    expect(moved).to_length(5)

    expect(redis.llen(jobs_queue.queue_name)).to_equal(5)
    expect(redis.zcard(Queue.SCHEDULED_QUEUE_NAME)).to_equal(5)

    for enqueued_id in enqueued_ids:
        expect(redis.exists(Queue.get_message_name(enqueued_id))).to_be_true()


def test_queue_group1(client):
    """Test dequeue from group with all queues enabled."""

    queue = client.application.monitor_queue
    expect(queue).not_to_be_null()

    enqueued_id = queue.enqueue(Categories.Monitor, "something", other="öther")

    redis = client.application.redis
    expect(redis.llen(queue.queue_name)).to_equal(1)

    job = client.application.queue_group.dequeue()

    assert_queue_message(queue, 0, enqueued_id)

    expect(job.id).to_equal(enqueued_id)
    expect(job.queue).to_equal("fastlane:message-queue:monitor")
    expect(job.category).to_equal(Categories.Monitor)
    expect(job.args).to_length(1)
    expect(job.args[0]).to_equal("something")
    expect(job.kwargs).to_include("other")
    expect(job.kwargs["other"]).to_equal("öther")


def test_is_enqueued1(client):
    """Test is enqueued returns False for an invalid job."""
    queue = client.application.jobs_queue

    expect(queue.is_enqueued("invalid-id")).to_be_false()


def test_is_enqueued2(client):
    """Test is enqueued returns True for an enqueued job."""
    queue = client.application.jobs_queue
    expect(queue).not_to_be_null()

    enqueued_id = queue.enqueue(Categories.Job, "something", other="öther")
    expect(queue.is_enqueued(enqueued_id)).to_be_true()


def test_is_enqueued3(client):
    """Test is enqueued returns False for a scheduled job."""
    queue = client.application.jobs_queue
    expect(queue).not_to_be_null()

    enqueued_id = queue.enqueue_in("5s", Categories.Job, "something", other="öther")
    expect(queue.is_enqueued(enqueued_id)).to_be_false()


def test_is_scheduled1(client):
    """Test is scheduled returns False for an invalid job."""
    queue = client.application.jobs_queue

    expect(queue.is_scheduled("invalid-id")).to_be_false()


def test_is_scheduled2(client):
    """Test is scheduled returns True for a scheduled job."""
    queue = client.application.jobs_queue
    expect(queue).not_to_be_null()

    enqueued_id = queue.enqueue_in("5s", Categories.Job, "something", other="öther")
    expect(queue.is_scheduled(enqueued_id)).to_be_true()


def test_is_scheduled3(client):
    """Test is scheduled returns False for an enqueued job."""
    queue = client.application.jobs_queue
    expect(queue).not_to_be_null()

    enqueued_id = queue.enqueue(Categories.Job, "something", other="öther")
    expect(queue.is_scheduled(enqueued_id)).to_be_false()


def test_deschedule1(client):
    """Test deschedule removes job from scheduling queue."""
    queue = client.application.jobs_queue
    redis = client.application.redis

    enqueued_id = queue.enqueue_in("5s", Categories.Job, "something", other="öther")

    expect(queue.deschedule(enqueued_id)).to_be_true()

    expect(
        redis.zrangebylex(
            Queue.SCHEDULED_QUEUE_NAME, f"[{enqueued_id}", f"[{enqueued_id}"
        )
    ).to_be_empty()
    key = Queue.get_message_name(enqueued_id)
    expect(redis.exists(key)).to_equal(False)


def test_deschedule2(client):
    """Test deschedule works event if job's not scheduled."""
    queue = client.application.jobs_queue
    redis = client.application.redis

    expect(queue.deschedule("invalid_id")).to_be_false()
    expect(redis.zcard(Queue.SCHEDULED_QUEUE_NAME)).to_equal(0)
    key = Queue.get_message_name("invalid_id")
    expect(redis.exists(key)).to_equal(False)
