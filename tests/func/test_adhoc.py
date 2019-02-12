# Standard Library
from uuid import uuid4

# 3rd Party
from preggy import expect

import tests.func.base  # NOQA pylint: disable=unused-import


def test_get_tasks(client):
    """
    Given API and Worker are UP
    When I submit a new job
    Then I can see its results in API
    """

    task_id = uuid4()

    status, body, headers = client.post(
        f'/tasks/{task_id}/', data={
            "image": "ubuntu",
            "command": "ls -lah",
        })

    print(status, body, headers)
    expect(status).to_equal(200)
