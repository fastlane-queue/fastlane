# 3rd Party
from flask import (
    Blueprint,
    Response,
    current_app,
    g,
    jsonify,
    render_template,
    request,
    url_for,
)
from rq_scheduler import Scheduler

# Fastlane
from fastlane.api.helpers import return_error
from fastlane.models import Job, JobExecution

bp = Blueprint("execution", __name__)  # pylint: disable=invalid-name


@bp.route("/tasks/<task_id>/jobs/<job_id>/executions/<execution_id>/", methods=("GET",))
def get_job_execution(task_id, job_id, execution_id):
    logger = g.logger.bind(
        operation="get_job_execution",
        task_id=task_id,
        job_id=job_id,
        execution_id=execution_id,
    )

    logger.debug("Getting job...")
    job = Job.get_by_id(task_id=task_id, job_id=job_id)

    if job is None:
        msg = f"Task ({task_id}) or Job ({job_id}) not found."

        return return_error(msg, "get_job_execution", status=404, logger=logger)

    execution = job.get_execution_by_id(execution_id)

    if execution is None:
        msg = f"Job Execution ({execution_id}) not found in job ({job_id})."

        return return_error(msg, "get_job_execution", status=404, logger=logger)

    logger.debug("Job execution retrieved successfully...")

    return format_execution_details(job.task, job, execution)


def format_execution_details(task, job, execution, shallow=False):
    task_id = str(task.task_id)

    if shallow:
        execution_url = url_for(
            "execution.get_job_execution",
            task_id=task_id,
            job_id=str(job.job_id),
            execution_id=str(execution.execution_id),
            _external=True,
        )

        details = {"id": str(execution.execution_id), "url": execution_url}
    else:
        details = execution.to_dict(include_log=True, include_error=True)

    job_url = url_for(
        "task.get_job", task_id=task_id, job_id=str(job.job_id), _external=True
    )
    task_url = url_for("task.get_task", task_id=task_id, _external=True)

    return jsonify(
        {
            "task": {"id": task_id, "url": task_url},
            "job": {"id": str(job.job_id), "url": job_url},
            "execution": details,
        }
    )


def retrieve_execution_details(task_id, job_id, execution_id=None, get_data_fn=None):
    if get_data_fn is None:
        get_data_fn = lambda execution: execution.log  # noqa: E731

    logger = g.logger.bind(operation="get_response", task_id=task_id, job_id=job_id)

    logger.debug("Getting job...")
    job = Job.get_by_id(task_id=task_id, job_id=job_id)

    if job is None:
        msg = f"Task ({task_id}) or Job ({job_id}) not found."

        return return_error(
            msg, "retrieve_execution_details", status=404, logger=logger
        )

    if not job.executions:
        msg = f"No executions found in job ({job_id})."

        return return_error(
            msg, "retrieve_execution_details", status=400, logger=logger
        )

    if execution_id is None:
        execution = job.get_last_execution()
    else:
        execution = job.get_execution_by_id(execution_id)

    if not execution:
        msg = "No executions found in job with specified arguments."

        return return_error(
            msg, "retrieve_execution_details", status=400, logger=logger
        )

    headers = {"Fastlane-Exit-Code": str(execution.exit_code)}

    if execution.status in [JobExecution.Status.running, JobExecution.Status.enqueued]:
        logs = ""
    else:
        logs = get_data_fn(execution)

    return Response(headers=headers, response=logs, status=200)


def stdout_func(execution):
    return execution.log


def stderr_func(execution):
    return execution.error


def logs_func(execution):
    if execution.status not in [
        JobExecution.Status.running,
        JobExecution.Status.enqueued,
    ]:
        return f"{execution.log}\n-=-\n{execution.error}"

    return ""


@bp.route(
    "/tasks/<task_id>/jobs/<job_id>/executions/<execution_id>/stdout/", methods=("GET",)
)
def get_job_execution_stdout(task_id, job_id, execution_id):
    return retrieve_execution_details(task_id, job_id, execution_id, stdout_func)


@bp.route(
    "/tasks/<task_id>/jobs/<job_id>/executions/<execution_id>/stderr/", methods=("GET",)
)
def get_job_execution_stderr(task_id, job_id, execution_id):
    return retrieve_execution_details(task_id, job_id, execution_id, stderr_func)


@bp.route(
    "/tasks/<task_id>/jobs/<job_id>/executions/<execution_id>/logs/", methods=("GET",)
)
def get_job_execution_logs(task_id, job_id, execution_id):
    return retrieve_execution_details(task_id, job_id, execution_id, logs_func)


def perform_stop_job_execution(job, execution, logger, stop_schedule=True):
    if "retries" in job.metadata:
        logger.info("Cleared any further job retries.")
        job.metadata["retry_count"] = job.metadata["retries"] + 1
        job.save()

    scheduler = Scheduler("jobs", connection=current_app.redis)

    if (
        stop_schedule
        and "enqueued_id" in job.metadata
        and job.metadata["enqueued_id"] in scheduler
    ):
        logger.info("Removed job from scheduling.")
        scheduler.cancel(job.metadata["enqueued_id"])
        job.scheduled = False

    if execution is not None:
        if execution.status == JobExecution.Status.running:
            logger.debug("Stopping current execution...")
            executor = current_app.executor
            executor.stop_job(job.task, job, execution)
            logger.debug("Current execution stopped.")

            if execution.error is None:
                execution.error = ""
            execution.error += "\nUser stopped job execution manually."
            execution.status = JobExecution.Status.failed

    job.save()

    logger.debug("Job stopped.")

    return True, None


@bp.route(
    "/tasks/<task_id>/jobs/<job_id>/executions/<execution_id>/stop/",
    methods=("POST",),
    strict_slashes=False,
)
def stop_job_execution(task_id, job_id, execution_id):
    logger = g.logger.bind(
        operation="stop_job_execution",
        task_id=task_id,
        job_id=job_id,
        execution_id=execution_id,
    )

    logger.debug("Getting job...")
    job = Job.get_by_id(task_id=task_id, job_id=job_id)

    if job is None:
        msg = f"Task ({task_id}) or Job ({job_id}) not found."

        return return_error(msg, "stop_job_execution", status=404, logger=logger)

    execution = job.get_execution_by_id(execution_id)

    if execution is None:
        msg = f"Job Execution ({execution_id}) not found in Job ({job_id})."

        return return_error(msg, "stop_job_execution", status=404, logger=logger)

    _, response = perform_stop_job_execution(
        job, execution=execution, logger=logger, stop_schedule=False
    )

    if response is not None:
        return response

    return format_execution_details(job.task, job, execution, shallow=True)


@bp.route("/tasks/<task_id>/jobs/<job_id>/executions/<execution_id>/stream/")
def stream_job(task_id, job_id, execution_id):
    if request.url.startswith("https"):
        protocol = "wss"
    else:
        protocol = "ws"

    url = url_for(
        "execution.stream_job",
        task_id=task_id,
        job_id=job_id,
        execution_id=execution_id,
        external=True,
    )
    url = "/".join(url.split("/")[:-2])
    ws_url = "%s://%s/%s/ws/" % (protocol, request.host.rstrip("/"), url.lstrip("/"))

    return render_template(
        "stream.html",
        task_id=task_id,
        job_id=job_id,
        execution_id=execution_id,
        ws_url=ws_url,
    )
