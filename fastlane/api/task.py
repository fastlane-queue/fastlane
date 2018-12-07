import time

from flask import (
    Blueprint,
    abort,
    current_app,
    g,
    jsonify,
    render_template,
    request,
    url_for,
)
from rq_scheduler import Scheduler

from fastlane.models.job import Job
from fastlane.models.task import Task

bp = Blueprint("task", __name__)


@bp.route("/tasks/<task_id>", methods=("GET",))
def get_task(task_id):
    logger = g.logger.bind(task_id=task_id)

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
    logger = g.logger.bind(task_id=task_id, job_id=job_id)

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

    logger = g.logger.bind(task_id=task_id, job_id=job_id)

    logger.debug("Getting job...")
    job = Job.get_by_id(task_id=task_id, job_id=job_id)

    if job is None:
        logger.error("Job not found in task.")
        abort(404)

        return

    scheduler = Scheduler("jobs", connection=current_app.redis)

    if (
        "enqueued_id" not in job.metadata
        or job.metadata["enqueued_id"] not in scheduler
    ):
        msg = "Could not stop job since it's not recurring."
        logger.error(msg)
        abort(400)

        return msg

    scheduler.cancel(job.metadata["enqueued_id"])

    job.scheduled = False
    job.save()

    return jsonify({"taskId": task_id, "job": {"id": job_id}})


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
