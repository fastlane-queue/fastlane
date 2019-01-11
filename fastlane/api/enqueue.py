# Standard Library
from datetime import datetime, timezone

# 3rd Party
from flask import Blueprint, current_app, g, jsonify, make_response, request, url_for
from rq_scheduler import Scheduler

# Fastlane
from fastlane.models.task import Task
from fastlane.utils import parse_time
from fastlane.worker.job import run_job

try:
    from ujson import loads
except ImportError:
    from json import loads

bp = Blueprint("enqueue", __name__)  # pylint: disable=invalid-name


def get_details():
    details = request.get_json()

    if details is None and request.get_data():
        details = loads(request.get_data())

    return details


def create_job(details, task, logger):
    logger.debug("Creating job...")
    retries = details.get("retries", 0)
    expiration = details.get("expiration")

    # people to notify when job succeeds, fails or finishes
    notify = details.get("notify", {"succeeds": [], "fails": [], "finishes": []})

    # people to notify when job succeeds, fails or finishes
    webhooks = details.get("webhooks", {"succeeds": [], "fails": [], "finishes": []})

    # additional metadata
    metadata = details.get("metadata", {})

    if not isinstance(metadata, (dict,)):
        metadata = {}

    hard_limit = current_app.config["HARD_EXECUTION_TIMEOUT_SECONDS"]
    timeout = details.get("timeout", hard_limit)
    timeout = min(
        timeout, hard_limit
    )  # ensure  jobs can't specify more than hard limit

    j = task.create_job()
    j.metadata["retries"] = retries
    j.metadata["notify"] = notify
    j.metadata["webhooks"] = webhooks
    j.metadata["retry_count"] = 0
    j.metadata["expiration"] = expiration
    j.metadata["timeout"] = timeout
    j.metadata["envs"] = details.get("envs", {})

    if metadata:
        j.metadata["custom"] = metadata

    j.save()
    logger.debug("Job created successfully...", job_id=str(j.id))

    return j


def enqueue_job(task, job, image, command, start_at, start_in, cron, logger):
    scheduler = Scheduler("jobs", connection=current_app.redis)

    args = [task.task_id, str(job.id), image, command]

    queue_job_id = None

    if start_at is not None:
        future_date = datetime.utcfromtimestamp(int(start_at))
        logger.debug("Enqueuing job execution in the future...", start_at=future_date)
        result = scheduler.enqueue_at(future_date, run_job, *args)
        job.metadata["enqueued_id"] = str(result.id)
        queue_job_id = str(result.id)
        job.save()
        logger.info("Job execution enqueued successfully.", start_at=future_date)
    elif start_in is not None:
        future_date = datetime.now(tz=timezone.utc) + start_in
        logger.debug("Enqueuing job execution in the future...", start_at=future_date)
        result = scheduler.enqueue_at(future_date, run_job, *args)
        job.metadata["enqueued_id"] = str(result.id)
        queue_job_id = str(result.id)
        job.save()
        logger.info("Job execution enqueued successfully.", start_at=future_date)
    elif cron is not None:
        logger.debug("Enqueuing job execution using cron...", cron=cron)
        result = scheduler.cron(
            cron,  # A cron string (e.g. "0 0 * * 0")
            func=run_job,
            args=args,
            repeat=None,
            queue_name="jobs",
        )
        job.metadata["enqueued_id"] = str(result.id)
        queue_job_id = str(result.id)
        job.metadata["cron"] = cron
        job.scheduled = True
        job.save()
        logger.info("Job execution enqueued successfully.", cron=cron)
    else:
        logger.debug("Enqueuing job execution...")
        result = current_app.job_queue.enqueue(run_job, *args, timeout=-1)
        queue_job_id = result.id
        job.metadata["enqueued_id"] = result.id
        job.save()
        logger.info("Job execution enqueued successfully.")

    return queue_job_id


@bp.route("/tasks/<task_id>", methods=("POST",))
def create_task(task_id):
    details = get_details()

    if details is None or details == "":
        msg = "Failed to enqueue task because JSON body could not be parsed."
        g.logger.warn(msg)

        return make_response(msg, 400)

    image = details.get("image", None)
    command = details.get("command", None)

    if image is None or command is None:
        return make_response("image and command must be filled in the request.", 400)

    logger = g.logger.bind(task_id=task_id, image=image, command=command)

    logger.debug("Creating task...")
    task = Task.objects(task_id=task_id).modify(task_id=task_id, upsert=True, new=True)
    logger.info("Task created successfully.")

    j = create_job(details, task, logger)
    job_id = str(j.id)

    queue_job_id = None

    start_at = details.get("startAt", None)
    start_in = parse_time(details.get("startIn", None))
    cron = details.get("cron", None)

    if len(list(filter(lambda item: item is not None, (start_at, start_in, cron)))) > 1:
        return make_response(
            "Only ONE of 'startAt', 'startIn' and 'cron' should be in the request.", 400
        )

    queue_job_id = enqueue_job(
        task, j, image, command, start_at, start_in, cron, logger
    )

    job_url = url_for("task.get_job", task_id=task_id, job_id=job_id, _external=True)

    return jsonify(
        {
            "taskId": task_id,
            "jobId": job_id,
            "queueJobId": queue_job_id,
            "jobUrl": job_url,
            "taskUrl": task.get_url(),
        }
    )
