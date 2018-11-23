import math
from datetime import datetime, timedelta

from flask import current_app
from rq_scheduler import Scheduler

from easyq.models.job import Job, JobExecution
from easyq.worker import ExecutionResult


def run_job(task_id, job_id, image, command):
    app = current_app
    logger = app.logger.bind(
        task_id=task_id, job_id=job_id, image=image, command=command
    )

    try:
        executor = app.load_executor()

        executions = executor.get_running_containers()

        job = Job.get_by_id(task_id, job_id)

        if job is None:
            logger.error("Job was not found with task id and job id.")

            return False

        tag = "latest"

        if ":" in image:
            image, tag = image.split(":")

        if not executor.validate_max_running_executions(task_id):
            logger.debug(
                "Maximum number of global container executions reached. Enqueuing job execution..."
            )
            args = [task_id, job_id, image, command]
            result = current_app.job_queue.enqueue(run_job, *args, timeout=-1)
            job.metadata["enqueued_id"] = result.id
            job.save()
            logger.info(
                "Job execution re-enqueued successfully due to max number of container executions."
            )

            return True

        logger = logger.bind(image=image, tag=tag)

        logger.debug("Changing job status...", status=JobExecution.Status.pulling)
        ex = job.create_execution(image=image, command=command)
        ex.status = JobExecution.Status.pulling
        job.save()
        logger.debug(
            "Job status changed successfully.", status=JobExecution.Status.pulling
        )
    except Exception as err:
        logger.error("Failed to create job execution. Skipping job...", error=err)
        raise err

    try:
        logger.info("Started processing job.")

        try:
            logger.debug("Downloading updated container image...", image=image, tag=tag)
            executor.update_image(job.task, job, ex, image, tag)
            logger.info("Image downloaded successfully.", image=image, tag=tag)
        except Exception as err:
            logger.error("Failed to download image.", error=err)
            ex.error = str(err)
            ex.status = JobExecution.Status.failed
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
            ex.status = JobExecution.Status.failed
            job.save()
            raise err

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
        ex.error = str(err)
        job.save()

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
    except Exception as err:
        logger.error("Failed to monitor job", error=err)
        raise err
