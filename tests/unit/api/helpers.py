# 3rd Party
from flask import Response, current_app
from preggy import assertion, utils

# Fastlane
from fastlane.helpers import loads
from fastlane.queue import Message, Queue


@assertion
def to_be_an_error_with(topic, status=500, msg=None, operation=None):
    """Asserts that `response from API is a proper error message`."""

    if not isinstance(topic, Response):
        raise AssertionError(
            f"Expected topic to be a flask.Response, not {type(topic)}."
        )

    if topic.status_code != status:
        raise AssertionError(
            f"Expected response's status code to equal {status}, but it was {topic.status_code}."
        )

    data = topic.data
    try:
        obj = loads(data)
    except ValueError:
        raise AssertionError(
            f"Expected response to be JSON, but it was not:\n\n{data}."
        )

    if operation is not None and obj.get("operation") != operation:
        raise AssertionError(
            f"Expected error operation to be {operation}, but it was {obj.get('operation')}."
        )

    if obj.get("error") != msg:
        raise AssertionError(
            f"Expected error message to be {msg}, but it was {obj.get('error')}."
        )


@assertion
def to_be_enqueued(topic):
    """Asserts that `job is enqueued`."""
    topic = utils.fix_string(topic)

    queue_job_id = utils.fix_string(topic["queueJobId"])

    hash_key = f"{Queue.QUEUE_NAME}:jobs"
    exists = current_app.redis.exists(hash_key)

    if not exists:
        raise AssertionError(
            f"Expected job '{queue_job_id}' to exist but it was not found"
        )

    message_ids = current_app.redis.lrange(hash_key, 0, -1)

    for message_id in message_ids:
        if message_id.decode("utf-8") == queue_job_id:
            return

    raise AssertionError(
        f"Expected job '{queue_job_id}' to be in the 'jobs' queue, but it was not found("
        f"found jobs: {','.join([message_id.decode('utf-8') for message_id in message_ids])})."
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
