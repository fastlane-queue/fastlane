# Standard Library
from json import loads
from uuid import uuid4
from datetime import datetime
import calendar

# 3rd Party
from preggy import expect

import tests.func.base  # NOQA isort:skip pylint:disable=unused-import


def test_scheduled1(client):
    """
    Given API and Worker are UP
    When I submit a scheduled job with specific timestamp
    Then I can see its results in API
    """

    task_id = uuid4()
    date = datetime.utcnow()
    unixtime = calendar.timegm(date.utctimetuple())

    status, body, _ = client.post(
        f"/tasks/{task_id}/",
        data={
            "image": "ubuntu",
            "command": "echo 'it works'",
            "startAt": unixtime + 5,
        })

    expect(status).to_equal(200)
    result = loads(body)
    expect(result["jobId"]).not_to_be_null()
    job_url = result["jobUrl"]

    meta = {}
    expect(job_url).to_have_execution(cli=client, execution=meta, timeout=30)

    expect(meta).to_include('url')
    expect(meta).to_include('executionId')

    expect(meta['url']).to_have_finished_with(
        status='done', log='it works', exitCode=0, cli=client)


def test_scheduled2(client):
    """
    Given API and Worker are UP
    When I submit a scheduled job in a few seconds
    Then I can see its results in API
    """

    task_id = uuid4()

    status, body, _ = client.post(
        f"/tasks/{task_id}/",
        data={
            "image": "ubuntu",
            "command": "echo 'it works'",
            "startIn": '2s',
        })

    expect(status).to_equal(200)
    result = loads(body)
    expect(result["jobId"]).not_to_be_null()
    job_url = result["jobUrl"]

    meta = {}
    expect(job_url).to_have_execution(cli=client, execution=meta, timeout=30)

    expect(meta).to_include('url')
    expect(meta).to_include('executionId')

    expect(meta['url']).to_have_finished_with(
        status='done', log='it works', exitCode=0, cli=client)
