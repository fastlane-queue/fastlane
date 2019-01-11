# Standard Library
from json import loads

# 3rd Party
from preggy import expect

# Fastlane
from fastlane.models.task import Task


def test_get_tasks(client):
    """Test getting tasks"""
    Task.create_task("my-task-1")
    Task.create_task("my-task-2")
    Task.create_task("my-task-3")

    resp = client.get("/tasks")
    expect(resp.status_code).to_equal(200)

    data = loads(resp.data)
    expect(data["items"]).to_length(3)
    expect(data["total"]).to_equal(3)
    expect(data["page"]).to_equal(1)
    expect(data["pages"]).to_equal(1)
    expect(data["perPage"]).to_equal(3)
    expect(data["hasNext"]).to_be_false()
    expect(data["hasPrev"]).to_be_false()


def test_get_tasks_data(client):
    """Test getting tasks resource data"""
    task = Task.create_task("my-task")

    resp = client.get("/tasks")

    data = loads(resp.data)
    task_data = data["items"][0]

    with client.application.app_context():
        expect(task_data.keys()).to_equal(task.to_dict().keys())


def test_get_tasks_pagination(client):
    """Test getting tasks pagination"""
    Task.create_task("my-task-1")
    Task.create_task("my-task-2")
    Task.create_task("my-task-3")
    Task.create_task("my-task-4")

    app = client.application
    server_name = app.config["SERVER_NAME"]

    resp = client.get("/tasks?page=2")

    data = loads(resp.data)
    expect(data["total"]).to_equal(4)
    expect(data["page"]).to_equal(2)
    expect(data["hasNext"]).to_be_false()
    expect(data["hasPrev"]).to_be_true()
    expect(data["prevUrl"]).to_equal(f"http://{server_name}/tasks?page=1")
    expect(data["nextUrl"]).to_be_null()


def test_get_tasks_pagination_404_invalid_pages(client):
    """
    Test getting tasks pagination should respond 404 when page is invalid
    """
    resp1 = client.get("/tasks?page=asdasdas")
    expect(resp1.status_code).to_equal(404)

    resp2 = client.get("/tasks?page=1019021")
    expect(resp2.status_code).to_equal(404)

    resp3 = client.get("/tasks?page=0")
    expect(resp3.status_code).to_equal(404)

    resp4 = client.get("/tasks?page=-1")
    expect(resp4.status_code).to_equal(404)
