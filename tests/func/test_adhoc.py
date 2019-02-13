# Standard Library
import time
from json import loads
from uuid import uuid4

# 3rd Party
from preggy import assertion, expect

import tests.func.base  # NOQA isort:skip pylint:disable=unused-import


@assertion
def to_have_finished_with(topic, client, timeout=10, **kw):
    def validate(execution, **arguments):
        for key, value in arguments.items():
            val = execution[kw]
            if isinstance(val, (bytes, str)):
                val = val.strip()
            if val != value:
                raise AssertionError(
                    'Execution did not match expectations! \n'
                    f'{key}:\n\tExpected: {value}\nActual:   {val}')

    start = time.time()

    last_obj = None
    while time.time() - start < timeout:
        status_code, body, _ = client.get(topic, absolute=True)

        if status_code != 200:
            raise AssertionError(
                f"{topic} could not be found (status: {status_code}).")

        last_obj = loads(body)

        try:
            if validate(last_obj['execution']):
                return
        except AssertionError:
            pass

        time.sleep(0.5)

    validate(last_obj['execution'])


def test_get_tasks(client):
    """
    Given API and Worker are UP
    When I submit a new job
    Then I can see its results in API
    """

    task_id = uuid4()

    status, body, _ = client.post(
        f"/tasks/{task_id}/",
        data={
            "image": "ubuntu",
            "command": "echo 'it works'"
        })

    expect(status).to_equal(200)
    result = loads(body)
    expect(result["executionId"]).not_to_be_null()
    execution_url = result["executionUrl"]

    expect(execution_url).to_have_finished_with(
        status='done', log='it works', exit_code=0, client=client)
