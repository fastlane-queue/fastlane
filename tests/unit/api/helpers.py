# 3rd Party
from flask import Response, current_app
from preggy import assertion, utils

# Fastlane
from fastlane.helpers import loads


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
