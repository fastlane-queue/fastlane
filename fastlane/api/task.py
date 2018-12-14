import time

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    g,
    jsonify,
    render_template,
    request,
    url_for,
)
from rq_scheduler import Scheduler

from fastlane.models.job import Job, JobExecution
from fastlane.models.task import Task
from fastlane.worker.job import run_job

bp = Blueprint("task", __name__)


@bp.route("/tasks/<task_id>", methods=("GET",))
def get_task(task_id):
    logger = g.logger.bind(operation="get_task", task_id=task_id)

    logger.debug("Getting job...")
    task = Task.get_by_task_id(task_id)

    if task is None:
        logger.error("Task not found.")
        abort(404)

        return
    logger.debug("Task retrieved successfully...")

    jobs = []

    for job_id in task.jobs:
        url = url_for(
            "task.get_job", task_id=task_id, job_id=str(job_id.id), _external=True
        )
        job = {"id": str(job_id.id), "url": url}
        jobs.append(job)

    return jsonify({"taskId": task_id, "jobs": jobs})


@bp.route("/tasks/<task_id>/jobs/<job_id>", methods=("GET",))
def get_job(task_id, job_id):
    logger = g.logger.bind(operation="get_job", task_id=task_id, job_id=job_id)

    logger.debug("Getting job...")
    job = Job.get_by_id(task_id=task_id, job_id=job_id)

    if job is None:
        logger.error("Job not found in task.")
        abort(404)

        return
    logger.debug("Job retrieved successfully...")

    details = job.to_dict(
        include_log=True,
        include_error=True,
        blacklist=current_app.config["ENV_BLACKLISTED_WORDS"].lower().split(","),
    )

    task_url = url_for("task.get_task", task_id=task_id, _external=True)

    return jsonify({"task": {"id": task_id, "url": task_url}, "job": details})


@bp.route("/tasks/<task_id>/jobs/<job_id>/stop", methods=("POST",))
def stop_job(task_id, job_id):
    logger = g.logger.bind(operation="stop", task_id=task_id, job_id=job_id)

    logger.debug("Getting job...")
    job = Job.get_by_id(task_id=task_id, job_id=job_id)

    if job is None:
        logger.error("Job not found in task.")
        abort(404)

        return

    execution = job.get_last_execution()

    if execution is not None and execution.status == JobExecution.Status.running:
        logger.debug("Stopping current execution...")
        executor = current_app.load_executor()
        executor.stop_job(job.task, job, execution)
        logger.debug("Current execution stopped.")

    scheduler = Scheduler("jobs", connection=current_app.redis)

    if "enqueued_id" in job.metadata and job.metadata["enqueued_id"] in scheduler:
        scheduler.cancel(job.metadata["enqueued_id"])
        job.scheduled = False
        job.save()

    logger.debug("Job stopped.")

    return get_job_summary(task_id, job_id)


@bp.route("/tasks/<task_id>/jobs/<job_id>/retry", methods=("POST",))
def retry_job(task_id, job_id):
    logger = g.logger.bind(operation="retry", task_id=task_id, job_id=job_id)

    logger.debug("Getting job...")
    job = Job.get_by_id(task_id=task_id, job_id=job_id)

    if job is None:
        logger.error("Job not found in task.")
        abort(404)

        return

    execution = job.get_last_execution()

    if execution is None:
        logger.error("No execution yet to retry.")
        abort(Response(response="No execution yet to retry.", status=400))

        return

    scheduler = Scheduler("jobs", connection=current_app.redis)

    if "enqueued_id" in job.metadata and job.metadata["enqueued_id"] in scheduler:
        msg = "Can't retry a scheduled job."
        logger.error(msg)
        abort(Response(response=msg, status=400))

        return

    if execution.status == JobExecution.Status.running:
        logger.debug("Stopping current execution...")
        executor = current_app.load_executor()
        executor.stop_job(job.task, job, execution)
        logger.debug("Current execution stopped.")

    execution.status = JobExecution.Status.failed
    job.save()

    logger.debug("Enqueuing job execution...")
    args = [task_id, job_id, execution.image, execution.command]
    result = current_app.job_queue.enqueue(run_job, *args, timeout=-1)
    job.metadata["enqueued_id"] = result.id
    job.save()
    logger.info("Job execution enqueued successfully.")

    return get_job_summary(task_id, job_id)


def get_job_summary(task_id, job_id):
    job_url = url_for("task.get_job", task_id=task_id, job_id=job_id, _external=True)
    task_url = url_for("task.get_task", task_id=task_id, _external=True)

    return jsonify(
        {"taskId": task_id, "jobId": job_id, "jobUrl": job_url, "taskUrl": task_url}
    )


@bp.route("/tasks/<task_id>/jobs/<job_id>/stream")
def stream_job(task_id, job_id):
    if request.url.startswith("https"):
        protocol = "wss"
    else:
        protocol = "ws"

    url = url_for("task.stream_job", task_id=task_id, job_id=job_id, external=True)
    url = "/".join(url.split("/")[:-1])
    ws_url = "%s://%s/%s/ws" % (protocol, request.host.rstrip("/"), url.lstrip("/"))

    return render_template("stream.html", task_id=task_id, job_id=job_id, ws_url=ws_url)


def get_response(task_id, job_id, get_data_fn):
    logger = g.logger.bind(operation="get_response", task_id=task_id, job_id=job_id)

    logger.debug("Getting job...")
    job = Job.get_by_id(task_id=task_id, job_id=job_id)

    if job is None:
        logger.error("Job not found in task.")
        abort(404)

        return

    if not job.executions:
        logger.error("No executions found in job.")
        abort(400)

        return

    execution = job.get_last_execution()

    headers = {"Fastlane-Exit-Code": str(execution.exit_code)}

    return Response(headers=headers, response=get_data_fn(execution), status=200)


@bp.route("/tasks/<task_id>/jobs/<job_id>/stdout")
def stdout(task_id, job_id):
    return get_response(task_id, job_id, lambda execution: execution.log)


@bp.route("/tasks/<task_id>/jobs/<job_id>/stderr")
def stderr(task_id, job_id):
    return get_response(task_id, job_id, lambda execution: execution.error)
