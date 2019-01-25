# Standard Library
from datetime import datetime

# 3rd Party
import croniter
import pkg_resources
from flask import Blueprint, current_app, jsonify, url_for

# Fastlane
from fastlane.models import Job, Task

bp = Blueprint("status", __name__, url_prefix="/status")  # pylint: disable=invalid-name


@bp.route("/", methods=("GET",))
def status():
    executor = current_app.executor
    version = pkg_resources.get_distribution("fastlane").version
    metadata = {"hosts": [], "containers": {"running": []}}

    containers = executor.get_running_containers()

    for host, port, container_id in containers["running"]:
        metadata["containers"]["running"].append(
            {"host": host, "port": port, "id": container_id}
        )

    metadata["hosts"] = [] + containers["available"] + containers["unavailable"]
    metadata["queues"] = {"jobs": {}, "monitor": {}, "error": {}}

    for queue in ["jobs", "monitor", "error"]:
        jobs_queue_size = current_app.redis.llen(f"rq:queue:{queue}")
        metadata["queues"][queue]["length"] = jobs_queue_size

    metadata["tasks"] = {"count": Task.objects.count()}

    metadata["jobs"] = {"count": Job.objects.count()}

    metadata["jobs"]["scheduled"] = []
    scheduled_jobs = Job.objects(scheduled=True).all()

    metadata["fastlane"] = {
        "version": version,
        "executor": current_app.config["EXECUTOR"],
    }

    for job in scheduled_jobs:
        j = job.to_dict(include_executions=False)

        itr = croniter.croniter(job.metadata["cron"], datetime.utcnow())
        j["nextScheduledAt"] = itr.get_next(datetime).isoformat()

        task_id = job.task.task_id

        job_url = url_for(
            "task.get_job", task_id=task_id, job_id=str(job.id), _external=True
        )
        j["url"] = job_url

        stop_job_url = url_for(
            "task.stop_job", task_id=task_id, job_id=str(job.id), _external=True
        )
        j["stopUrl"] = stop_job_url

        task_url = url_for("task.get_task", task_id=task_id, _external=True)
        del j["taskId"]
        j["task"] = {"id": task_id, "url": task_url}

        metadata["jobs"]["scheduled"].append(j)

    return jsonify(metadata), 200
