from uuid import uuid4

from preggy import expect

from fastlane.models.job import Job
from fastlane.models.task import Task


def test_job_create(client):
    """Test creating a new job"""

    task_id = str(uuid4())

    t = Task.create_task(task_id)
    j = t.create_job()

    expect(j.job_id).to_equal(str(j.id))
    expect(j.created_at).not_to_be_null()
    expect(j.last_modified_at).not_to_be_null()
    expect(j.executions).to_be_empty()


def test_job_get_by_job_id(client):
    """Test getting a job by id"""

    task_id = str(uuid4())
    t = Task.create_task(task_id)

    j = t.create_job()

    topic = Job.get_by_id(task_id, j.job_id)
    expect(topic).not_to_be_null()
    expect(topic.job_id).to_equal(str(j.id))

    topic = Job.get_by_id("invalid", "invalid")
    expect(topic).to_be_null()
