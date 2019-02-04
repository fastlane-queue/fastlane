# 3rd Party
from flask import Blueprint, current_app, g, jsonify, render_template, request, url_for
from rq_scheduler import Scheduler

# Fastlane
from fastlane.api.execution import (
    logs_func,
    perform_stop_job_execution,
    retrieve_execution_details,
    stderr_func,
    stdout_func,
)
from fastlane.api.helpers import return_error
from fastlane.models import Job, JobExecution, Task
from fastlane.worker.job import run_job

bp = Blueprint("task", __name__)  # pylint: disable=invalid-name


def get_current_page(logger):
    try:
        page = int(request.args.get("page", 1))

        if page <= 0:
            raise ValueError()

        return page, None
    except ValueError:
        msg = "Tasks pagination page param should be a positive integer."

        return None, return_error(msg, "get_tasks", status=400, logger=logger)


@bp.route("/tasks/", methods=("GET",))
def get_tasks():
    logger = g.logger.bind(operation="get_tasks")

    page, error = get_current_page(logger)

    if error:
        return error

    per_page = current_app.config["PAGINATION_PER_PAGE"]

    logger.debug(f"Getting tasks page={page} per_page={per_page}...")
    paginator = Task.get_tasks(page=page, per_page=per_page)

    logger.debug("Tasks retrieved successfully...")

    next_url = None

    if paginator.has_next:
        next_url = url_for("task.get_tasks", page=paginator.next_num, _external=True)

    prev_url = None

    if paginator.has_prev:
        prev_url = url_for("task.get_tasks", page=paginator.prev_num, _external=True)

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


@bp.route("/search/", methods=("GET",))
def search_tasks():
    logger = g.logger.bind(operation="search_tasks")

    query = request.args.get("query")

    if not query:
        msg = "The query param is required."

        return return_error(msg, "search_tasks", status=400, logger=logger)

    page, error = get_current_page(logger)

    if error:
        return error

    per_page = current_app.config["PAGINATION_PER_PAGE"]

    logger.debug(f"Getting tasks page={page} per_page={per_page}...")
    paginator = Task.search_tasks(query=query, page=page, per_page=per_page)

    logger.debug("Tasks retrieved successfully...")

    next_url = None

    if paginator.has_next:
        next_url = url_for(
            "task.search_tasks", query=query, page=paginator.next_num, _external=True
        )

    prev_url = None

    if paginator.has_prev:
        prev_url = url_for(
            "task.search_tasks", query=query, page=paginator.prev_num, _external=True
        )

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
        return return_error("Task not found.", "get_task", status=404, logger=logger)

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
        return return_error(
            "Job not found in task.", "get_task", status=404, logger=logger
        )

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


@bp.route(
    "/tasks/<task_id>/jobs/<job_id>/stop/", methods=("POST",), strict_slashes=False
)
def stop_job(task_id, job_id):
    logger = g.logger.bind(operation="stop_job", task_id=task_id, job_id=job_id)

    logger.debug("Getting job...")
    job = Job.get_by_id(task_id=task_id, job_id=job_id)

    if job is None:
        return return_error(
            "Job not found in task.", "stop_job", status=404, logger=logger
        )

    execution = job.get_last_execution()

    _, response = perform_stop_job_execution(
        job, execution=execution, logger=logger, stop_schedule=True
    )

    if response is not None:
        return response

    return get_job_summary(task_id, job_id)


@bp.route(
    "/tasks/<task_id>/jobs/<job_id>/retry/", methods=("POST",), strict_slashes=False
)
def retry_job(task_id, job_id):
    logger = g.logger.bind(operation="retry", task_id=task_id, job_id=job_id)

    logger.debug("Getting job...")
    job = Job.get_by_id(task_id=task_id, job_id=job_id)

    if job is None:
        return return_error(
            "Job not found in task.", "retry_job", status=404, logger=logger
        )

    execution = job.get_last_execution()

    if execution is None:
        return return_error(
            "No execution yet to retry.", "retry_job", status=400, logger=logger
        )

    scheduler = Scheduler("jobs", connection=current_app.redis)

    if "enqueued_id" in job.metadata and job.metadata["enqueued_id"] in scheduler:
        msg = "Can't retry a scheduled job."

        return return_error(msg, "retry_job", status=400, logger=logger)

    if execution.status == JobExecution.Status.running:
        logger.debug("Stopping current execution...")
        executor = current_app.executor
        executor.stop_job(job.task, job, execution)
        logger.debug("Current execution stopped.")

    execution.status = JobExecution.Status.failed
    job.save()

    new_exec = job.create_execution(execution.image, execution.command)
    new_exec.status = JobExecution.Status.enqueued

    logger.debug("Enqueuing job execution...")
    args = [task_id, job_id, new_exec.execution_id, execution.image, execution.command]
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
    url = "/".join(url.split("/")[:-2])
    ws_url = "%s://%s/%s/ws/" % (protocol, request.host.rstrip("/"), url.lstrip("/"))

    return render_template("stream.html", task_id=task_id, job_id=job_id, ws_url=ws_url)


@bp.route("/tasks/<task_id>/jobs/<job_id>/stdout/")
def stdout(task_id, job_id):
    return retrieve_execution_details(task_id, job_id, get_data_fn=stdout_func)


@bp.route("/tasks/<task_id>/jobs/<job_id>/stderr/")
def stderr(task_id, job_id):
    return retrieve_execution_details(task_id, job_id, get_data_fn=stderr_func)


@bp.route("/tasks/<task_id>/jobs/<job_id>/logs/")
def logs(task_id, job_id):
    return retrieve_execution_details(task_id, job_id, get_data_fn=logs_func)
