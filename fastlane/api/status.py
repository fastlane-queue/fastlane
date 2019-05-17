# Standard Library
from datetime import datetime

# 3rd Party
import croniter
import pkg_resources
from flask import Blueprint, current_app, jsonify, url_for

# Fastlane
from fastlane.models import Job, Task
from fastlane.models.categories import QueueNames
from fastlane.queue import Queue
from fastlane.utils import from_unix

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
    metadata["queues"] = {}

    for queue_name in [
        QueueNames.Job,
        QueueNames.Monitor,
        QueueNames.Webhook,
        QueueNames.Notify,
    ]:
        queue = getattr(current_app, f"{queue_name}_queue")
        jobs_queue_size = current_app.redis.llen(queue.queue_name)
        metadata["queues"][queue_name] = {"length": jobs_queue_size}

    next_scheduled = current_app.redis.zrange(
        Queue.SCHEDULED_QUEUE_NAME, 0, 0, withscores=True
    )

    if not next_scheduled:
        next_timestamp = None
        next_human = None
    else:
        next_timestamp = next_scheduled[0][1]
        next_human = from_unix(next_timestamp).isoformat()

    metadata["queues"]["scheduled"] = {
        "length": current_app.redis.zcard(Queue.SCHEDULED_QUEUE_NAME),
        "nextTimeStamp": next_timestamp,
        "nextHumanReadableDate": next_human,
    }

    metadata["tasks"] = {"count": Task.objects.count()}

    metadata["jobs"] = {"count": Job.objects.count()}

    metadata["jobs"]["scheduled"] = []
    scheduled_jobs = Job.objects(scheduled=True).all()

    metadata["fastlane"] = {
        "version": version,
        "executor": current_app.config["EXECUTOR"],
    }

    for job in scheduled_jobs:
        j = job.to_dict(
            include_executions=False,
            blacklist_fn=current_app.blacklist_words_fn,
        )

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
