from uuid import uuid4

from preggy import expect

from easyq.models.job import Job


def test_job_create(client):
    """Test creating a new job"""

    job_id = str(uuid4())

    j = Job.create_job(job_id)
    expect(j.job_id).to_equal(job_id)
    expect(j.created_at).not_to_be_null()
    expect(j.last_modified_at).not_to_be_null()

    expect(j.container_id).to_be_null()
    expect(j.status).to_equal(Job.Status.enqueued)

    created_at = j.created_at
    last_mod = j.last_modified_at

    j.save()
    expect(j.created_at).to_equal(created_at)
    expect(j.last_modified_at).to_be_greater_than(last_mod)


def test_job_create2(client):
    """Test creating a new job fails when no job_id provided"""
    msg = "Job ID is required and can't be None or empty."
    with expect.error_to_happen(RuntimeError, message=msg):
        Job.create_job(None)

    with expect.error_to_happen(RuntimeError, message=msg):
        Job.create_job("")


def test_job_get_by_job_id(client):
    """Test getting a job by job id"""
    job_id = str(uuid4())
    j = Job.create_job(job_id)

    topic = Job.get_by_job_id(j.job_id)
    expect(topic.id).to_equal(j.id)


def test_job_get_by_job_id2(client):
    """Test getting a job by job id returns None if no job exists"""
    job_id = str(uuid4())

    topic = Job.get_by_job_id(job_id)
    expect(topic).to_be_null()


def test_job_get_by_job_id3(client):
    """Test getting a job by job id fails if job id is empty"""
    msg = "Job ID is required and can't be None or empty."
    with expect.error_to_happen(RuntimeError, message=msg):
        Job.get_by_job_id(None)

    with expect.error_to_happen(RuntimeError, message=msg):
        Job.get_by_job_id("")
