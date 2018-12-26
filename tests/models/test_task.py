# Standard Library
from uuid import uuid4

# 3rd Party
from mongoengine.errors import ValidationError
from preggy import expect

# Fastlane
from fastlane.models.task import Task


def test_task_create(client):
    """Test creating a new task"""

    task_id = str(uuid4())

    t = Task.create_task(task_id)
    expect(t.task_id).to_equal(task_id)
    expect(t.created_at).not_to_be_null()
    expect(t.last_modified_at).not_to_be_null()

    created_at = t.created_at
    last_mod = t.last_modified_at

    t.save()
    expect(t.created_at).to_equal(created_at)
    expect(t.last_modified_at).to_be_greater_than(last_mod)


def test_task_create2(client):
    """Test creating a new task fails when no task_id provided"""
    msg = "ValidationError (Task:None) (Field is required: ['task_id'])"
    with expect.error_to_happen(ValidationError, message=msg):
        Task.create_task(None)

    with expect.error_to_happen(ValidationError, message=msg):
        Task.create_task("")


def test_task_get_by_task_id(client):
    """Test getting a task by task id"""
    task_id = str(uuid4())
    t = Task.create_task(task_id)

    topic = Task.get_by_task_id(t.task_id)
    expect(topic.id).to_equal(t.id)


def test_task_get_by_task_id2(client):
    """Test getting a task by task id returns None if no task exists"""
    task_id = str(uuid4())

    topic = Task.get_by_task_id(task_id)
    expect(topic).to_be_null()


def test_task_get_by_task_id3(client):
    """Test getting a task by task id fails if task id is empty"""
    msg = "Task ID is required and can't be None or empty."
    with expect.error_to_happen(RuntimeError, message=msg):
        Task.get_by_task_id(None)

    with expect.error_to_happen(RuntimeError, message=msg):
        Task.get_by_task_id("")
