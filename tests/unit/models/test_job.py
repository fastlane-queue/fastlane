# Standard Library
from uuid import uuid4

# 3rd Party
from preggy import expect
from tests.fixtures.models import JobExecutionFixture, JobFixture

# Fastlane
from fastlane.models import Job, JobExecution, Task
from fastlane.utils import dumps, loads


# Must inject client to connect to redis and DB
def test_job_create(client):  # pylint: disable=unused-argument
    """Test creating a new job"""

    task_id = str(uuid4())

    task = Task.create_task(task_id)
    job = task.create_job("image", "command")

    expect(job.created_at).not_to_be_null()
    expect(job.last_modified_at).not_to_be_null()
    expect(job.executions).to_be_empty()
    expect(job.image).to_equal("image")
    expect(job.command).to_equal("command")


def test_job_create_or_update1(client):  # pylint: disable=unused-argument
    """Test creating or updating a new job"""

    task_id = str(uuid4())
    job_id = str(uuid4())

    task = Task.create_task(task_id)
    job = task.create_or_update_job(job_id, "image", "command")

    expect(job.job_id).to_equal(str(job_id))
    expect(job.created_at).not_to_be_null()
    expect(job.last_modified_at).not_to_be_null()
    expect(job.executions).to_be_empty()


def test_job_create_or_update2(client):  # pylint: disable=unused-argument
    """Test creating or updating an existing job"""

    task_id = str(uuid4())

    task = Task.create_task(task_id)
    job = task.create_job("image", "command")

    job_id = str(job.job_id)
    new_job = task.create_or_update_job(job_id, "image", "command")

    expect(str(new_job.id)).to_equal(str(job.id))
    expect(new_job.created_at).not_to_be_null()
    expect(new_job.last_modified_at).not_to_be_null()
    expect(new_job.executions).to_be_empty()


def test_job_get_by_job_id(client):  # pylint: disable=unused-argument
    """Test getting a job by id"""

    task_id = str(uuid4())
    task = Task.create_task(task_id)

    job = task.create_job("image", "command")

    topic = Job.get_by_id(task_id, job.job_id)
    expect(topic).not_to_be_null()
    expect(topic.job_id).to_equal(str(job.job_id))

    topic = Job.get_by_id("invalid", "invalid")
    expect(topic).to_be_null()


def test_get_unfinished_executions(client):
    with client.application.app_context():
        app = client.application
        app.redis.flushall()

        for status in [
            JobExecution.Status.enqueued,
            JobExecution.Status.pulling,
            JobExecution.Status.running,
            JobExecution.Status.done,
            JobExecution.Status.failed,
        ]:
            _, job, execution = JobExecutionFixture.new_defaults()
            execution.status = status
            execution.save()
            job.save()

        topic = Job.get_unfinished_executions(app)
        expect(topic).to_length(2)

        for (_, execution) in topic:
            expect(execution).to_be_instance_of(JobExecution)
            expect(
                execution.status
                in [JobExecution.Status.pulling, JobExecution.Status.running]
            ).to_be_true()


def test_get_unscheduled_jobs1(client):
    """Test gets unscheduled job without enqueued_id"""

    with client.application.app_context():
        task_id = str(uuid4())
        data = {"image": "ubuntu", "command": "ls", "cron": "* * * * *"}
        response = client.post(
            f"/tasks/{task_id}/", data=dumps(data), follow_redirects=True
        )

        expect(response.status_code).to_equal(200)
        obj = loads(response.data)
        job_id = obj["jobId"]
        Job.get_by_id(task_id, job_id)

        job = JobFixture.new(metadata={"cron": "* * * * *"})

        unscheduled_jobs = Job.get_unscheduled_jobs(client.application)

        expect(unscheduled_jobs).to_length(1)
        expect(unscheduled_jobs[0].job_id).to_equal(job.job_id)
