from datetime import datetime

import croniter
from flask import Blueprint, current_app, jsonify, url_for

from fastlane.models.job import Job
from fastlane.models.task import Task

bp = Blueprint("status", __name__, url_prefix="/status")


@bp.route("/", methods=("GET",))
def status():
    executor = current_app.load_executor()
    status = {"hosts": [], "containers": {"running": []}}

    containers = executor.get_running_containers()

    for host, port, container_id in containers["running"]:
        status["containers"]["running"].append(
            {"host": host, "port": port, "id": container_id}
        )

    status["hosts"] = containers["available"]

    status["queues"] = {"jobs": {}, "monitor": {}, "error": {}}

    for queue in ["jobs", "monitor", "error"]:
        jobs_queue_size = current_app.redis.llen(f"rq:queue:{queue}")
        status["queues"][queue]["length"] = jobs_queue_size

    status["tasks"] = {"count": Task.objects.count()}

    status["jobs"] = {"count": Job.objects.count()}

    status["jobs"]["scheduled"] = []
    scheduled_jobs = Job.objects(scheduled=True).all()

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

        status["scheduled"].append(j)

    return jsonify(status), 200
