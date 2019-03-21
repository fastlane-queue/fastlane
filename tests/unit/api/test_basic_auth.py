# Standard Library
from base64 import b64encode
from json import loads

# 3rd Party
from preggy import expect

# Fastlane
from fastlane.models.task import Task


def test_get_tasks(auth_client):
    """Test getting tasks"""
    Task.create_task("my-task-1")
    Task.create_task("my-task-2")
    Task.create_task("my-task-3")

    userAndPass = b64encode(b"test:auth").decode("ascii")
    headers = {"Authorization": "Basic %s" % userAndPass}

    resp = auth_client.get("/tasks/", headers=headers)
    expect(resp.status_code).to_equal(200)

    data = loads(resp.data)
    expect(data["items"]).to_length(3)
    expect(data["total"]).to_equal(3)
    expect(data["page"]).to_equal(1)
    expect(data["pages"]).to_equal(1)
    expect(data["perPage"]).to_equal(3)
    expect(data["hasNext"]).to_be_false()
    expect(data["hasPrev"]).to_be_false()
