# 3rd Party
from flask import Blueprint, g, jsonify, make_response, url_for

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
