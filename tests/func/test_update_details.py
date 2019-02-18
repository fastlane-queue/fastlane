# Standard Library
import calendar
from datetime import datetime
from json import loads
from uuid import uuid4

# 3rd Party
from preggy import expect

import tests.func.base  # NOQA isort:skip pylint:disable=unused-import


def test_update1(client):
    """
    Given API and Worker are UP
    When I update a job's details
    Then I can see its updated in API
    """

    task_id = uuid4()
    date = datetime.utcnow()
    unixtime = calendar.timegm(date.utctimetuple())

    status, body, _ = client.post(
        f"/tasks/{task_id}/",
        data={
            "image": "ubuntu",
            "command": "echo 'it works'",
            "startAt": unixtime + 5000,
        },
    )

    expect(status).to_equal(200)
    result = loads(body)
    expect(result["jobId"]).not_to_be_null()
    job_id = result["jobId"]

    status, body, _ = client.put(
        f"/tasks/{task_id}/jobs/{job_id}/",
        data={
            "image": "ubuntu",
            "command": "echo 'it was updated'",
            "startAt": unixtime + 2,
        },
    )

    result = loads(body)
    expect(result["jobId"]).not_to_be_null()
    job_url = result["jobUrl"]

    meta = {}
    expect(job_url).to_have_execution(cli=client, execution=meta, timeout=30)

    expect(meta).to_include("url")
    expect(meta).to_include("executionId")

    expect(meta["url"]).to_have_finished_with(
        status="done", log="it was updated", exitCode=0, cli=client
    )
