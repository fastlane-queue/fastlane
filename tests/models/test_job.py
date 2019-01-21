# Standard Library
from uuid import uuid4

# 3rd Party
from preggy import expect

# Fastlane
from fastlane.models import Job, Task


# Must inject client to connect to redis and DB
def test_job_create(client):  # pylint: disable=unused-argument
    """Test creating a new job"""

    task_id = str(uuid4())

    task = Task.create_task(task_id)
    job = task.create_job()

    expect(job.created_at).not_to_be_null()
    expect(job.last_modified_at).not_to_be_null()
    expect(job.executions).to_be_empty()


def test_job_create_or_update1(client):  # pylint: disable=unused-argument
    """Test creating or updating a new job"""

    task_id = str(uuid4())
    job_id = str(uuid4())

    task = Task.create_task(task_id)
    job = task.create_or_update_job(job_id)

    expect(job.job_id).to_equal(str(job_id))
    expect(job.created_at).not_to_be_null()
    expect(job.last_modified_at).not_to_be_null()
    expect(job.executions).to_be_empty()


def test_job_create_or_update2(client):  # pylint: disable=unused-argument
    """Test creating or updating an existing job"""

    task_id = str(uuid4())

    task = Task.create_task(task_id)
    job = task.create_job()

    job_id = str(job.job_id)
    new_job = task.create_or_update_job(job_id)

    expect(str(new_job.id)).to_equal(str(job.id))
    expect(new_job.created_at).not_to_be_null()
    expect(new_job.last_modified_at).not_to_be_null()
    expect(new_job.executions).to_be_empty()


def test_job_get_by_job_id(client):  # pylint: disable=unused-argument
    """Test getting a job by id"""

    task_id = str(uuid4())
    task = Task.create_task(task_id)

    job = task.create_job()

    topic = Job.get_by_id(task_id, job.job_id)
    expect(topic).not_to_be_null()
    expect(topic.job_id).to_equal(str(job.job_id))

    topic = Job.get_by_id("invalid", "invalid")
    expect(topic).to_be_null()
