import math
from datetime import datetime, timedelta

from flask import current_app
from rq_scheduler import Scheduler

from easyq.models.job import Job
from easyq.worker import ExecutionResult


def run_job(task_id, job_id, image, command):
    app = current_app
    logger = app.logger.bind(
        task_id=task_id, job_id=job_id, image=image, command=command
    )

    try:
        executor = app.load_executor()

        job = Job.get_by_id(task_id, job_id)

        if job is None:
            logger.error("Job was not found with task id and job id.")

            return False

        tag = "latest"

        if ":" in image:
            image, tag = image.split(":")

        logger = logger.bind(image=image, tag=tag)

        logger.debug("Changing job status...", status=Job.Status.pulling)
        ex = job.create_execution(image=image, command=command)
        ex.status = Job.Status.pulling
        job.save()
        logger.debug("Job status changed successfully.", status=Job.Status.pulling)

        logger.info("Started processing job.")

        try:
            logger.debug("Downloading updated container image...", image=image, tag=tag)
            executor.update_image(job.task, job, ex, image, tag)
            logger.info("Image downloaded successfully.", image=image, tag=tag)
        except Exception as err:
            logger.error("Failed to download image.", error=err)
            ex.error = str(err)
            ex.status = Job.Status.failed
            job.save()
            raise err

        logger.debug(
            "Running command in container...", image=image, tag=tag, command=command
        )
        try:
            executor.run(job.task, job, ex, image, tag, command)
            logger.info(
                "Container started successfully.", image=image, tag=tag, command=command
            )
        except Exception as err:
            logger.error("Failed to run command", error=err)
            ex.error = str(err)
            ex.status = Job.Status.failed
            job.save()
            raise err

        logger.debug("Changing job status...", status=Job.Status.running)
        ex.status = Job.Status.running
        job.save()
        logger.debug("Job status changed successfully.", status=Job.Status.running)

        app.monitor_queue.enqueue(
            monitor_job, task_id, job_id, ex.execution_id, timeout=-1
        )

        return True
    except Exception as err:
        logger.error("Failed to run job", error=err)
        raise err


def monitor_job(task_id, job_id, execution_id):
    try:
        app = current_app
        executor = app.load_executor()

        job = Job.get_by_id(task_id, job_id)
        logger = app.logger.bind(task_id=task_id, job_id=job_id)

        if job is None:
            logger.error("Failed to retrieve task or job.")

            return False

        execution = job.get_execution_by_id(execution_id)
        result = executor.get_result(job.task, job, execution)
        logger.info(
            "Container result obtained.",
            container_status=result.status,
            container_exit_code=result.exit_code,
        )

        if result.status in (
            ExecutionResult.Status.created,
            ExecutionResult.Status.running,
        ):
            scheduler = Scheduler("monitor", connection=app.redis)
            logger.info(
                "Job has not finished. Retrying monitoring in the future.",
                container_status=result.status,
                seconds=1,
            )

            interval = timedelta(seconds=5)
            scheduler.enqueue_in(interval, monitor_job, task_id, job_id, execution_id)

            return

        if (
            result.exit_code != 0
            and "retry_count" in job.metadata
            and job.metadata["retry_count"] < job.metadata["retries"]
        ):
            retry_logger = logger.bind(
                exit_code=result.exit_code,
                retry_count=job.metadata["retry_count"],
                retries=job.metadata["retries"],
            )
            retry_logger.debug("Job failed. Enqueuing job retry...")
            job.metadata["retry_count"] += 1

            scheduler = Scheduler("jobs", connection=current_app.redis)

            args = [task_id, job_id, execution.image, execution.command]
            dt = datetime.utcnow() + timedelta(
                seconds=math.pow(2, job.metadata["retry_count"])
            )
            enqueued = scheduler.enqueue_at(dt, run_job, *args)

            job.metadata["enqueued_id"] = enqueued.id
            job.save()

            retry_logger.info("Job execution enqueued successfully.")

        execution.finished_at = datetime.utcnow()
        execution.status = Job.Status.done
        execution.exit_code = result.exit_code
        execution.log = result.log.decode("utf-8")
        execution.error = result.error.decode("utf-8")

        logger.debug(
            "Job finished. Storing job details in mongo db.",
            status=execution.status,
            log=result.log,
            error=result.error,
        )
        job.save()
        logger.info("Job details stored in mongo db.", status=execution.status)
    except Exception as err:
        logger.error("Failed to monitor job", error=err)
        raise err
