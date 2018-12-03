import calendar
import math
import time
from datetime import datetime, timedelta

from flask import current_app
from rq_scheduler import Scheduler

from fastlane.models.job import Job, JobExecution
from fastlane.worker import ExecutionResult


def validate_max_concurrent(executor, task_id, job, image, command, logger):
    if not executor.validate_max_running_executions(task_id):
        logger.debug(
            "Maximum number of global container executions reached. Enqueuing job execution..."
        )
        args = [task_id, job.id, image, command]
        result = current_app.job_queue.enqueue(run_job, *args, timeout=-1)
        job.metadata["enqueued_id"] = result.id
        job.save()
        logger.info(
            "Job execution re-enqueued successfully due to max number of container executions."
        )

        return False

    return True


def validate_expiration(job, ex, logger):
    d = datetime.utcnow()
    unixtime = calendar.timegm(d.utctimetuple())

    if (
        job.metadata.get("expiration") is not None
        and job.metadata["expiration"] < unixtime
    ):
        expiration_utc = datetime.utcfromtimestamp(job.metadata["expiration"])
        ex.status = JobExecution.Status.expired
        ex.error = f"Job was supposed to be done before {expiration_utc.isoformat()}, but was started at {d.isoformat()}."
        ex.finished_at = datetime.utcnow()
        job.save()
        logger.info(
            "Job execution canceled due to being expired.",
            job_expiration=job.metadata["expiration"],
            current_ts=unixtime,
        )

        return False

    return True


def download_image(executor, job, ex, image, tag, command, logger):
    try:
        logger.debug("Downloading updated container image...", image=image, tag=tag)
        before = time.time()
        executor.update_image(job.task, job, ex, image, tag)
        ellapsed = time.time() - before
        logger.info(
            "Image downloaded successfully.", image=image, tag=tag, ellapsed=ellapsed
        )
    except Exception as err:
        logger.error("Failed to download image.", error=err)
        ex.error = str(err)
        ex.status = JobExecution.Status.failed
        job.save()

        current_app.report_error(
            err,
            metadata=dict(
                operation="Downloading Image",
                task_id=job.task.task_id,
                job_id=job.id,
                execution_id=ex.execution_id,
                image=image,
                tag=tag,
                command=command,
            ),
        )

        return False

    return True


def run_container(executor, job, ex, image, tag, command, logger):
    logger.debug(
        "Running command in container...", image=image, tag=tag, command=command
    )
    try:
        ex.started_at = datetime.utcnow()
        job.save()

        before = time.time()
        executor.run(job.task, job, ex, image, tag, command)
        ellapsed = time.time() - before
        logger.info(
            "Container started successfully.",
            image=image,
            tag=tag,
            command=command,
            ellapsed=ellapsed,
        )
    except Exception as err:
        logger.error("Failed to run command", error=err)
        ex.error = str(err)
        ex.status = JobExecution.Status.failed
        job.save()

        current_app.report_error(
            err,
            metadata=dict(
                operation="Running Container",
                task_id=job.task.task_id,
                job_id=job.id,
                execution_id=ex.execution_id,
                image=image,
                tag=tag,
                command=command,
            ),
        )

        return False

    return True


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

        if not validate_max_concurrent(executor, task_id, job, image, command, logger):
            return False

        tag = "latest"

        if ":" in image:
            image, tag = image.split(":")

        logger = logger.bind(image=image, tag=tag)

        logger.debug("Changing job status...", status=JobExecution.Status.pulling)
        ex = job.create_execution(image=image, command=command)
        ex.status = JobExecution.Status.enqueued
        job.save()

        logger.debug(
            "Job status changed successfully.", status=JobExecution.Status.pulling
        )
        logger = logger.bind(execution_id=ex.execution_id)
    except Exception as err:
        logger.error("Failed to create job execution. Skipping job...", error=err)
        current_app.report_error(
            err,
            metadata=dict(task_id=task_id, job_id=job_id, image=image, command=command),
        )

        return False

    try:
        if not validate_expiration(job, ex, logger):
            return False

        logger.info("Started processing job.")

        if not download_image(executor, job, ex, image, tag, command, logger):
            return False

        if not run_container(executor, job, ex, image, tag, command, logger):
            return False

        logger.debug("Changing job status...", status=JobExecution.Status.running)
        ex.status = JobExecution.Status.running
        job.save()
        logger.debug(
            "Job status changed successfully.", status=JobExecution.Status.running
        )

        app.monitor_queue.enqueue(
            monitor_job, task_id, job_id, ex.execution_id, timeout=-1
        )

        return True
    except Exception as err:
        logger.error("Failed to run job", error=err)
        ex.status = JobExecution.Status.failed
        ex.error = f"Job failed to run with error: {str(err)}"
        job.save()

        current_app.report_error(
            err,
            metadata=dict(
                operation="Running Container",
                task_id=task_id,
                job_id=job_id,
                execution_id=ex.execution_id,
                image=image,
                tag=tag,
                command=command,
            ),
        )


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
            ellapsed = (datetime.utcnow() - execution.started_at).total_seconds()

            if ellapsed > job.metadata["timeout"]:
                execution.finished_at = datetime.utcnow()
                execution.status = JobExecution.Status.timedout
                execution.error = f"Job execution timed out after {ellapsed} seconds."

                executor.stop_job(job.task, job, execution)

                logger.debug(
                    "Job execution timed out. Storing job details in mongo db.",
                    status=execution.status,
                    ellapsed=ellapsed,
                    error=result.error,
                )
                job.save()
                logger.info("Job execution timed out.", status=execution.status)

                return False

            scheduler = Scheduler("monitor", connection=app.redis)
            logger.info(
                "Job has not finished. Retrying monitoring in the future.",
                container_status=result.status,
                seconds=1,
            )

            interval = timedelta(seconds=5)
            scheduler.enqueue_in(interval, monitor_job, task_id, job_id, execution_id)

            return True

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
            factor = app.config["EXPONENTIAL_BACKOFF_FACTOR"]
            min_backoff = app.config["EXPONENTIAL_BACKOFF_MIN_MS"] / 1000.0
            delta = timedelta(seconds=min_backoff)

            if job.metadata["retries"] > 0:
                delta = timedelta(
                    seconds=math.pow(factor, job.metadata["retry_count"]) * min_backoff
                )
            dt = datetime.utcnow() + delta
            enqueued = scheduler.enqueue_at(dt, run_job, *args)

            job.metadata["enqueued_id"] = enqueued.id
            job.save()

            retry_logger.info("Job execution enqueued successfully.")

            # still need to finish current execution as the retry
            # will be a new execution

        execution.finished_at = datetime.utcnow()
        execution.status = JobExecution.Status.done
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

        return True
    except Exception as err:
        logger.error("Failed to monitor job", error=err)
        current_app.report_error(
            err,
            metadata=dict(
                operation="Monitoring Job",
                task_id=task_id,
                job_id=job_id,
                execution_id=execution_id,
            ),
        )

        raise err
