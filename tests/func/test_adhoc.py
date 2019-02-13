# Standard Library
from json import loads
from uuid import uuid4

# 3rd Party
from preggy import expect

import tests.func.base  # NOQA isort:skip pylint:disable=unused-import


def test_adhoc1(client):
    """
    Given API and Worker are UP
    When I submit a new job that ends successfully
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
        status='done', log='it works', exitCode=0, cli=client)


def test_adhoc2(client):
    """
    Given API and Worker are UP
    When I submit a new job that fails
    Then I can see its results in API
    """

    task_id = uuid4()

    status, body, _ = client.post(
        f"/tasks/{task_id}/",
        data={
            "image": "ubuntu",
            "command": """bash -c 'echo "it failed" && exit 123'""",
        })

    expect(status).to_equal(200)
    result = loads(body)
    expect(result["executionId"]).not_to_be_null()
    execution_url = result["executionUrl"]

    expect(execution_url).to_have_finished_with(
        status='failed', log='it failed', error='', exitCode=123, cli=client)
