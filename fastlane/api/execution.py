# 3rd Party
from flask import Blueprint, Response, g, jsonify, make_response, url_for

# Fastlane
from fastlane.models.job import Job

bp = Blueprint("execution", __name__)  # pylint: disable=invalid-name


@bp.route("/tasks/<task_id>/jobs/<job_id>/executions/<execution_id>", methods=("GET",))
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
        logger.error(msg)

        return make_response(msg, 404)

    execution = job.get_execution_by_id(execution_id)

    if execution is None:
        msg = f"Job Execution ({execution_id}) not found in job ({job_id})."
        logger.error(msg)

        return make_response(msg, 404)

    logger.debug("Job execution retrieved successfully...")

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
        logger.error(msg)

        return make_response(msg, 404)

    if not job.executions:
        logger.error("No executions found in job.")

        return make_response("No executions found in job.", 400)

    if execution_id is None:
        execution = job.get_last_execution()
    else:
        execution = job.get_execution_by_id(execution_id)

    if not execution:
        msg = "No executions found in job with specified arguments."
        logger.error(msg)

        return make_response(msg, 404)

    headers = {"Fastlane-Exit-Code": str(execution.exit_code)}

    return Response(headers=headers, response=get_data_fn(execution), status=200)


@bp.route(
    "/tasks/<task_id>/jobs/<job_id>/executions/<execution_id>/stdout/", methods=("GET",)
)
def get_job_execution_stdout(task_id, job_id, execution_id):
    return retrieve_execution_details(task_id, job_id, execution_id)


@bp.route(
    "/tasks/<task_id>/jobs/<job_id>/executions/<execution_id>/stderr/", methods=("GET",)
)
def get_job_execution_stderr(task_id, job_id, execution_id):
    return retrieve_execution_details(
        task_id, job_id, execution_id, lambda execution: execution.error
    )


@bp.route(
    "/tasks/<task_id>/jobs/<job_id>/executions/<execution_id>/logs/", methods=("GET",)
)
def get_job_execution_logs(task_id, job_id, execution_id):
    func = lambda execution: f"{execution.log}\n-=-\n{execution.error}"  # NOQA: 731

    return retrieve_execution_details(task_id, job_id, execution_id, func)
