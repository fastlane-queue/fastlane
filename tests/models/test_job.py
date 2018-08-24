from uuid import uuid4

from mongoengine.errors import ValidationError
from preggy import expect

from easyq.models.job import Job
from easyq.models.task import Task


def test_job_create(client):
    """Test creating a new job"""

    task_id = str(uuid4())
    job_id = str(uuid4())

    t = Task.create_task(task_id, image='image', command='command')
    j = t.create_job(job_id)

    expect(j.job_id).to_equal(job_id)
    expect(j.created_at).not_to_be_null()
    expect(j.last_modified_at).not_to_be_null()
    expect(j.image).to_equal('image')
    expect(j.command).to_equal('command')

    expect(j.container_id).to_be_null()
    expect(j.status).to_equal(Job.Status.enqueued)


def test_job_create2(client):
    """Test creating a new job fails when no job_id provided"""

    task_id = str(uuid4())
    t = Task.create_task(task_id, image='image', command='command')

    msg = f"ValidationError (Task:{t.pk}) (job_id.Field is required: ['jobs'])"
    with expect.error_to_happen(ValidationError, message=msg):
        t.create_job(None)

    with expect.error_to_happen(ValidationError, message=msg):
        t.create_job("")


def test_job_get_by_job_id(client):
    """Test getting a job by job id"""

    task_id = str(uuid4())
    t = Task.create_task(task_id, image='image', command='command')

    job_id = str(uuid4())
    j = t.create_job(job_id)

    topic = t.get_job_by_job_id(j.job_id)
    expect(topic).not_to_be_null()
    expect(topic.job_id).to_equal(job_id)

    topic = t.get_job_by_job_id('invalid')
    expect(topic).to_be_null()
