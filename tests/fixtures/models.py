# Standard Library
from uuid import uuid4


class TaskFixture:
    @staticmethod
    def new(task_id):
        from fastlane.models.task import Task

        return Task.create_task(task_id)


class JobFixture:
    @staticmethod
    def new(job_id=None, task_id=None, task=None, metadata=None, scheduled=False):
        if task_id is None:
            task_id = str(uuid4())

        if task is None:
            task = TaskFixture.new(task_id)

        if metadata is None:
            metadata = {}

        job = task.create_job()

        if job_id is not None:
            job.job_id = job_id

        job.metadata = metadata
        job.scheduled = scheduled
        job.save()

        return job


class JobExecutionFixture:
    @staticmethod
    def new(
        image,
        command,
        execution_id=None,
        status=None,
        log=None,
        error=None,
        exit_code=None,
        job=None,
        task=None,
        metadata=None,
    ):
        if job is None:
            if task is None:
                task = TaskFixture.new(str(uuid4()))

            job = JobFixture.new(task=task)

        if metadata is None:
            metadata = {}

        execution = job.create_execution(image, command)
        execution.metadata = metadata

        if execution_id is not None:
            execution.execution_id = execution_id

        if status is not None:
            execution.status = status

        if log is not None:
            execution.log = log

        if error is not None:
            execution.error = error

        if exit_code is not None:
            execution.exit_code = exit_code

        job.save()

        return job, execution
