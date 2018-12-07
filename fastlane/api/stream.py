import time
from multiprocessing import Process

from flask import Blueprint, current_app

from fastlane.models.job import Job, JobExecution

bp = Blueprint("stream", __name__)


def stream_log(executor, task_id, job, ex, ws):
    if not ws.closed and ex.status == JobExecution.Status.done:
        ws.send("EXIT CODE: %s\n" % ex.exit_code)
        ws.send(ex.log)
        ws.close(message="wsdone")

        return

    if not ws.closed and ex.status == JobExecution.Status.failed:
        ws.send("EXIT CODE: %s\n" % ex.exit_code)
        ws.send(ex.error)
        ws.close(message="wsdone")

        return

    if not ws.closed and ex.status != JobExecution.Status.running:
        ws.close(message="wsretry")

        return

    for log in executor.get_streaming_logs(task_id, job, ex):
        ws.send(log)

    ws.close(message="wsdone")


@bp.route("/tasks/<task_id>/jobs/<job_id>/ws")
def ws(ws, task_id, job_id):
    executor = current_app.load_executor()
    logger = current_app.logger.bind(task_id=task_id, job_id=job_id)
    job = Job.get_by_id(task_id=task_id, job_id=job_id)

    if job is None:
        logger.error("Job not found in task.")
        ws.close()

        return

    ex = job.get_last_execution()

    if ex is None:
        logger.error("No executions found in job.")
        ws.close(message="wsretry")

        return

    p = Process(target=stream_log, args=(executor, task_id, job, ex, ws))
    p.start()

    while not ws.closed:
        time.sleep(10)

    p.terminate()
