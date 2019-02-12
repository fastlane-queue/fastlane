# Standard Library
import time
from multiprocessing import Process

# 3rd Party
from flask import Blueprint, current_app

# Fastlane
from fastlane.models import Job, JobExecution
from fastlane.worker.errors import ContainerUnavailableError

bp = Blueprint("stream", __name__)  # pylint: disable=invalid-name


def stream_log(executor, task_id, job, ex, websocket):
    try:
        if (
            not websocket.closed
            and ex.status == JobExecution.Status.done
            or ex.status == JobExecution.Status.failed
        ):
            websocket.send("EXIT CODE: %s\n" % ex.exit_code)
            websocket.send(ex.log)
            websocket.send("\n-=-\n")
            websocket.send(ex.error)
            websocket.close(message="wsdone")

            return

        if not websocket.closed and ex.status != JobExecution.Status.running:
            websocket.close(message="wsretry")

            return

        for log in executor.get_streaming_logs(task_id, job, ex):
            if websocket.closed:
                return
            websocket.send(log)
    except BrokenPipeError:
        websocket.close(message="wsretry")

        return
    except ContainerUnavailableError as err:
        current_app.report_error(
            err,
            metadata=dict(
                operation="Job Execution Stream",
                task_id=task_id,
                job_id=job.job_id,
                execution_id=ex.execution_id,
            ),
        )
        websocket.close(message="wsretry")

        return

    websocket.close(message="wsdone")


def process_job_execution_logs(websocket, task_id, job_id, execution_id, logger):
    job = Job.get_by_id(task_id=task_id, job_id=job_id)

    if job is None:
        logger.error(f"Job ({job_id}) not found in task ({task_id}).")
        websocket.close()

        return

    if execution_id is None:
        execution = job.get_last_execution()
    else:
        execution = job.get_execution_by_id(execution_id)

    if execution is None:
        logger.error("No executions found in job ({execution_id}).")
        websocket.close(message="wsretry")

        return

    executor = current_app.executor

    process = Process(
        target=stream_log, args=(executor, task_id, job, execution, websocket)
    )
    process.start()

    while not websocket.closed:
        time.sleep(10)

    process.terminate()


@bp.route("/tasks/<task_id>/jobs/<job_id>/ws/")
def websocket_listen(websocket, task_id, job_id):
    logger = current_app.logger.bind(task_id=task_id, job_id=job_id)
    process_job_execution_logs(websocket, task_id, job_id, None, logger)


@bp.route("/tasks/<task_id>/jobs/<job_id>/executions/<execution_id>/ws/")
def websocket_execution_listen(websocket, task_id, job_id, execution_id):
    logger = current_app.logger.bind(task_id=task_id, job_id=job_id)
    process_job_execution_logs(websocket, task_id, job_id, execution_id, logger)
