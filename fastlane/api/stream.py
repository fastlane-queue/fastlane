# Standard Library
import time
from multiprocessing import Process

# 3rd Party
from flask import Blueprint, current_app

# Fastlane
from fastlane.models.job import Job, JobExecution

bp = Blueprint("stream", __name__)  # pylint: disable=invalid-name


def stream_log(executor, task_id, job, ex, websocket):
    if not websocket.closed and ex.status == JobExecution.Status.done:
        websocket.send("EXIT CODE: %s\n" % ex.exit_code)
        websocket.send(ex.log)
        websocket.close(message="wsdone")

        return

    if not websocket.closed and ex.status == JobExecution.Status.failed:
        websocket.send("EXIT CODE: %s\n" % ex.exit_code)
        websocket.send(ex.error)
        websocket.close(message="wsdone")

        return

    if not websocket.closed and ex.status != JobExecution.Status.running:
        websocket.close(message="wsretry")

        return

    for log in executor.get_streaming_logs(task_id, job, ex):
        websocket.send(log)

    websocket.close(message="wsdone")


@bp.route("/tasks/<task_id>/jobs/<job_id>/ws")
def websocket_listen(websocket, task_id, job_id):
    executor = current_app.executor
    logger = current_app.logger.bind(task_id=task_id, job_id=job_id)
    job = Job.get_by_id(task_id=task_id, job_id=job_id)

    if job is None:
        logger.error("Job not found in task.")
        websocket.close()

        return

    ex = job.get_last_execution()

    if ex is None:
        logger.error("No executions found in job.")
        websocket.close(message="wsretry")

        return

    process = Process(target=stream_log, args=(executor, task_id, job, ex, websocket))
    process.start()

    while not websocket.closed:
        time.sleep(10)

    process.terminate()
