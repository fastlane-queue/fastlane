# 3rd Party
from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    g,
    jsonify,
    make_response,
    render_template,
    request,
    url_for,
)
from rq_scheduler import Scheduler

# Fastlane
from fastlane.api.execution import retrieve_execution_details
from fastlane.models.job import Job, JobExecution
from fastlane.models.task import Task
from fastlane.worker.job import run_job

bp = Blueprint("task", __name__)  # pylint: disable=invalid-name


@bp.route("/tasks/", methods=("GET",))
def get_tasks():
    logger = g.logger.bind(operation="get_tasks")

    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        logger.error(f"Tasks pagination page param should be an integer.")
        abort(404)

    per_page = current_app.config["PAGINATION_PER_PAGE"]

    logger.debug(f"Getting tasks page={page} per_page={per_page}...")
    paginator = Task.get_tasks(page=page, per_page=per_page)

    logger.debug("Tasks retrieved successfully...")

    tasks_url = url_for("task.get_tasks", _external=True)
    next_url = None

    if paginator.has_next:
        next_url = f"{tasks_url}?page={paginator.next_num}"

    prev_url = None

    if paginator.has_prev:
        prev_url = f"{tasks_url}?page={paginator.prev_num}"

    data = {
        "items": [],
        "total": paginator.total,
        "page": paginator.page,
        "pages": paginator.pages,
        "perPage": paginator.per_page,
        "hasNext": paginator.has_next,
        "hasPrev": paginator.has_prev,
        "nextUrl": next_url,
        "prevUrl": prev_url,
    }

    for task in paginator.items:
        data["items"].append(task.to_dict())

    return jsonify(data)


@bp.route("/tasks/<task_id>/", methods=("GET",))
def get_task(task_id):
    logger = g.logger.bind(operation="get_task", task_id=task_id)

    logger.debug("Getting job...")
    task = Task.get_by_task_id(task_id)

    if task is None:
        logger.error("Task not found.")

        return make_response("Task not found", 404)

    logger.debug("Task retrieved successfully...")

    task_jobs = Job.objects(id__in=[str(job_id.id) for job_id in task.jobs])

    jobs = []

    for job in task_jobs:
        url = url_for(
            "task.get_job", task_id=task_id, job_id=str(job.job_id), _external=True
        )
        job = {"id": str(job.job_id), "url": url}
        jobs.append(job)

    return jsonify({"taskId": task_id, "jobs": jobs})


@bp.route("/tasks/<task_id>/jobs/<job_id>/", methods=("GET",))
def get_job(task_id, job_id):
    logger = g.logger.bind(operation="get_job", task_id=task_id, job_id=job_id)

    logger.debug("Getting job...")
    job = Job.get_by_id(task_id=task_id, job_id=job_id)

    if job is None:
        logger.error("Job not found in task.")

        return make_response("Job not found in task", 404)

    logger.debug("Job retrieved successfully...")

    details = job.to_dict(
        include_log=True,
        include_error=True,
        blacklist=current_app.config["ENV_BLACKLISTED_WORDS"].lower().split(","),
    )

    for execution in details["executions"]:
        exec_url = url_for(
            "execution.get_job_execution",
            task_id=task_id,
            job_id=job_id,
            execution_id=execution["executionId"],
            _external=True,
        )
        execution["url"] = exec_url

    task_url = url_for("task.get_task", task_id=task_id, _external=True)

    return jsonify({"task": {"id": task_id, "url": task_url}, "job": details})


@bp.route("/tasks/<task_id>/jobs/<job_id>/stop/", methods=("POST",))
def stop_job(task_id, job_id):
    logger = g.logger.bind(operation="stop", task_id=task_id, job_id=job_id)

    logger.debug("Getting job...")
    job = Job.get_by_id(task_id=task_id, job_id=job_id)

    if job is None:
        logger.error("Job not found in task.")

        return make_response("Job not found in task", 404)

    execution = job.get_last_execution()

    if execution is not None and execution.status == JobExecution.Status.running:
        logger.debug("Stopping current execution...")
        executor = current_app.executor
        executor.stop_job(job.task, job, execution)
        logger.debug("Current execution stopped.")

    if "retries" in job.metadata:
        job.metadata["retry_count"] = job.metadata["retries"] + 1
        job.save()

    scheduler = Scheduler("jobs", connection=current_app.redis)

    if "enqueued_id" in job.metadata and job.metadata["enqueued_id"] in scheduler:
        scheduler.cancel(job.metadata["enqueued_id"])
        job.scheduled = False

    logger.debug("Job stopped.")

    return get_job_summary(task_id, job_id)


@bp.route("/tasks/<task_id>/jobs/<job_id>/retry/", methods=("POST",))
def retry_job(task_id, job_id):
    logger = g.logger.bind(operation="retry", task_id=task_id, job_id=job_id)

    logger.debug("Getting job...")
    job = Job.get_by_id(task_id=task_id, job_id=job_id)

    if job is None:
        logger.error("Job not found in task.")

        return make_response("Job not found in task", 404)

    execution = job.get_last_execution()

    if execution is None:
        logger.error("No execution yet to retry.")

        return make_response("No execution yet to retry.", 400)

    scheduler = Scheduler("jobs", connection=current_app.redis)

    if "enqueued_id" in job.metadata and job.metadata["enqueued_id"] in scheduler:
        msg = "Can't retry a scheduled job."
        logger.error(msg)

        return make_response(msg, 400)

    if execution.status == JobExecution.Status.running:
        logger.debug("Stopping current execution...")
        executor = current_app.executor
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


@bp.route("/tasks/<task_id>/jobs/<job_id>/stream/")
def stream_job(task_id, job_id):
    if request.url.startswith("https"):
        protocol = "wss"
    else:
        protocol = "ws"

    url = url_for("task.stream_job", task_id=task_id, job_id=job_id, external=True)
    url = "/".join(url.split("/")[:-1])
    ws_url = "%s://%s/%s/ws" % (protocol, request.host.rstrip("/"), url.lstrip("/"))

    return render_template("stream.html", task_id=task_id, job_id=job_id, ws_url=ws_url)


@bp.route("/tasks/<task_id>/jobs/<job_id>/stdout/")
def stdout(task_id, job_id):
    return retrieve_execution_details(
        task_id, job_id, get_data_fn=lambda execution: execution.log
    )


@bp.route("/tasks/<task_id>/jobs/<job_id>/stderr/")
def stderr(task_id, job_id):
    return retrieve_execution_details(
        task_id, job_id, get_data_fn=lambda execution: execution.error
    )


@bp.route("/tasks/<task_id>/jobs/<job_id>/logs/")
def logs(task_id, job_id):
    func = lambda execution: f"{execution.logs}\n{execution.error}"  # NOQA: 731

    return retrieve_execution_details(task_id, job_id, get_data_fn=func)
