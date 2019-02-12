# Standard Library
import time
from json import loads
from uuid import uuid4

# 3rd Party
from preggy import assertion, expect

import tests.func.base  # NOQA isort:skip pylint:disable=unused-import


@assertion
def to_have_finished(topic, status, log, client, timeout=5000):
    start = time.time()
    actual_status = ""

    while actual_status != status and time.time() - start < timeout:
        status_code, body, _ = client.get(topic, absolute=True)

        if status_code != 200:
            raise AssertionError(f"{topic} could not be found (status: {status}).")

        obj = loads(body)

        actual_status = obj.get("execution", {}).get("status", "")
        actual_log = obj.get("execution", {}).get("log", "")

        if actual_log is None:
            actual_log = ""
        actual_log = actual_log.strip()

        if actual_status == status and actual_log == log:
            return

        time.sleep(0.5)

    raise AssertionError(
        f"{topic}\nstatus:\n\tEXPECTED:'{status}'\n\tACTUAL:  '{actual_status}'"
        f"\nlog:\n\tEXPECTED:'{log}'\n\tACTUAL:  '{actual_log}'"
    )


def test_get_tasks(client):
    """
    Given API and Worker are UP
    When I submit a new job
    Then I can see its results in API
    """

    task_id = uuid4()

    status, body, _ = client.post(
        f"/tasks/{task_id}/", data={"image": "ubuntu", "command": "echo 'it works'"}
    )

    expect(status).to_equal(200)
    result = loads(body)
    expect(result["executionId"]).not_to_be_null()
    execution_url = result["executionUrl"]

    expect(execution_url).to_have_finished(status="done", log="it works", client=client)
