# Standard Library
from uuid import uuid4


class TaskFixture:
    @staticmethod
    def new(task_id):
        from fastlane.models import Task

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
        task_id=None,
        task=None,
        metadata=None,
    ):
        if task_id is None:
            task_id = str(uuid4())

        if job is None:
            if task is None:
                task = TaskFixture.new(task_id)

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

    @staticmethod
    def new_defaults(
        image=None,
        command=None,
        task_id=None,
        container_id=None,
        docker_host=None,
        docker_port=None,
        log=None,
        error=None,
        exit_code=None,
        status=None,
    ):
        if task_id is None:
            task_id = f"test-{uuid4()}"

        if image is None:
            image = "image"

        if command is None:
            command = "command"

        if container_id is None:
            container_id = str(uuid4())

        if docker_host is None:
            docker_host = "host"

        if docker_port is None:
            docker_port = 1234

        job, execution = JobExecutionFixture.new(
            image,
            command,
            task_id=task_id,
            log=log,
            error=error,
            exit_code=exit_code,
            status=status,
            metadata={
                "docker_host": docker_host,
                "docker_port": docker_port,
                "container_id": container_id,
            },
        )

        return job.task, job, execution
