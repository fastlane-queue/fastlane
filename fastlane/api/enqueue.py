# Standard Library
from uuid import UUID

# 3rd Party
from flask import Blueprint, current_app, g, jsonify, make_response, request, url_for

# Fastlane
from fastlane.helpers import loads
from fastlane.models import JobExecution, Task

bp = Blueprint("enqueue", __name__)  # pylint: disable=invalid-name


def get_details():
    try:
        details = request.get_json()
    except Exception:
        details = None

    if details is None and request.get_data():
        try:
            details = loads(request.get_data())
        except Exception:
            details = None

    return details


def get_ip_addr():
    if "X-Real-Ip" in request.headers:
        return request.headers["X-Real-Ip"]

    if "X-Forwarded-For" in request.headers:
        addresses = request.headers["X-Forwarded-For"].split(",")

        if addresses:
            return addresses[0]

    return request.remote_addr


def get_additional_dns_entries(details):
    additional_dns_entries = details.get("additionalDNSEntries")

    if not additional_dns_entries:
        return []

    return list(additional_dns_entries.items())


def create_job(details, task, logger, get_new_job_fn):
    logger.debug("Creating job...")
    retries = details.get("retries", 0)
    expiration = details.get("expiration")
    additional_dns_entries = get_additional_dns_entries(details)

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

    j = get_new_job_fn(task, details.get("image"), details.get("command"))

    j.metadata["retries"] = retries
    j.metadata["notify"] = notify
    j.metadata["webhooks"] = webhooks
    j.metadata["retry_count"] = 0
    j.metadata["expiration"] = expiration
    j.metadata["timeout"] = timeout
    j.metadata["envs"] = details.get("envs", {})
    j.metadata["additional_dns_entries"] = additional_dns_entries
    j.request_ip = get_ip_addr()

    if metadata:
        j.metadata["custom"] = metadata

    j.save()
    logger.debug("Job created successfully...", job_id=str(j.job_id))

    return j


def enqueue_job(task, job, image, command, start_at, start_in, cron, logger):
    execution = None
    queue_job_id = None

    if any([start_at, start_in, cron]):
        queue_job_id = job.schedule_job(
            current_app, dict(startAt=start_at, startIn=start_in, cron=cron)
        )

        return queue_job_id, execution

    logger.debug("Enqueuing job execution...")
    execution = job.create_execution(image, command)
    execution.request_ip = get_ip_addr()
    execution.status = JobExecution.Status.enqueued

    queue_job_id = job.enqueue(current_app, execution.execution_id)
    job.metadata["enqueued_id"] = queue_job_id
    execution.save()
    job.save()
    logger.info("Job execution enqueued successfully.")

    return queue_job_id, execution


def get_task_and_details(task_id):
    details = get_details()

    if details is None or details == "":
        msg = "Failed to enqueue task because JSON body could not be parsed."
        g.logger.warn(msg)

        return None, None, None, make_response(msg, 400)

    image = details.get("image", None)
    command = details.get("command", None)

    if image is None or command is None:
        return (
            None,
            None,
            None,
            make_response("image and command must be filled in the request.", 400),
        )

    logger = g.logger.bind(task_id=task_id, image=image, command=command)

    logger.debug("Creating task...")
    task = Task.objects(task_id=task_id).modify(task_id=task_id, upsert=True, new=True)
    logger.info("Task created successfully.")

    return task, details, logger, None


def validate_and_enqueue(details, task, job, logger):
    image = details.get("image", None)
    command = details.get("command", None)

    start_at = details.get("startAt", None)
    start_in = details.get("startIn", None)
    cron = details.get("cron", None)

    if len(list(filter(lambda item: item is not None, (start_at, start_in, cron)))) > 1:
        return (
            None,
            None,
            make_response(
                "Only ONE of 'startAt', 'startIn' and 'cron' should be in the request.",
                400,
            ),
        )

    result, execution = enqueue_job(
        task, job, image, command, start_at, start_in, cron, logger
    )

    return result, execution, None


@bp.route("/tasks/<task_id>/", methods=("POST",), strict_slashes=False)
def create_task(task_id):
    task, details, logger, response = get_task_and_details(task_id)

    if response is not None:
        return response

    job = create_job(
        details,
        task,
        logger,
        lambda task, image, command: task.create_job(image, command),
    )

    enqueued_id, execution, response = validate_and_enqueue(details, task, job, logger)

    if response is not None:
        return response

    return get_enqueue_response(task, job, execution, enqueued_id)


@bp.route("/tasks/<task_id>/jobs/<job_id>/", methods=("PUT",), strict_slashes=False)
def create_or_update_task(task_id, job_id):
    try:
        job_id = str(UUID(job_id))
    except ValueError:
        return make_response(
            f"The job_id {job_id} is not a valid UUID4. All job IDs must be UUID4.", 400
        )

    task, details, logger, response = get_task_and_details(task_id)

    if response is not None:
        return response

    job = create_job(
        details,
        task,
        logger,
        lambda task, image, command: task.create_or_update_job(job_id, image, command),
    )

    if "enqueued_id" in job.metadata:
        current_app.jobs_queue.deschedule(job.metadata["enqueued_id"])
        job.scheduled = False

    enqueued_id, execution, response = validate_and_enqueue(details, task, job, logger)

    if response is not None:
        return response

    return get_enqueue_response(task, job, execution, enqueued_id)


def get_enqueue_response(task, job, execution, enqueued_id):
    task_id = str(task.task_id)
    job_id = str(job.job_id)

    task_url = task.get_url()
    job_url = url_for("task.get_job", task_id=task_id, job_id=job_id, _external=True)

    if execution is None:
        execution_url = None
        execution_id = None
    else:
        execution_url = url_for(
            "execution.get_job_execution",
            task_id=task_id,
            job_id=job_id,
            execution_id=str(execution.execution_id),
            _external=True,
        )
        execution_id = str(execution.execution_id)

    return jsonify(
        {
            "taskId": task_id,
            "jobId": job_id,
            "executionId": execution_id,
            "executionUrl": execution_url,
            "queueJobId": enqueued_id,
            "jobUrl": job_url,
            "taskUrl": task_url,
        }
    )
