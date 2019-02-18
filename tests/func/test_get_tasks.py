# Standard Library
from json import loads
from uuid import uuid4

# 3rd Party
from preggy import expect

import tests.func.base  # NOQA isort:skip pylint:disable=unused-import


def test_get_tasks(client):
    """
    Given API and Worker are UP and Tasks exist
    When I ask for all tasks
    Then I can see them
    """

    task_id = uuid4()

    status, body, _ = client.post(
        f"/tasks/{task_id}/", data={"image": "ubuntu", "command": "echo 'it works'"}
    )
    expect(status).to_equal(200)

    status, body, _ = client.get(f"/tasks/")

    result = loads(body)

    expect(result["total"]).to_be_greater_than(0)
    expect(len(result["items"])).to_be_greater_than(0)
