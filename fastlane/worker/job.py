# Standard Library
import math
import smtplib
import time
import traceback
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# 3rd Party
from flask import current_app, url_for

# Fastlane
from fastlane.helpers import dumps, loads
from fastlane.models import Job, JobExecution
from fastlane.models.categories import Categories
from fastlane.utils import from_unix, to_unix
from fastlane.worker import ExecutionResult
from fastlane.worker.errors import HostUnavailableError
from fastlane.worker.webhooks import WebhooksDispatcher, WebhooksDispatchError


def validate_max_concurrent(
    executor, task_id, job, execution_id, image, command, logger
):
    if not executor.validate_max_running_executions(task_id):
        logger.debug(
            "Maximum number of global container executions reached. Enqueuing job execution..."
        )
        enqueued_id = job.enqueue(
            current_app, execution_id, image=image, command=command
        )
        job.metadata["enqueued_id"] = enqueued_id
        job.save()
        logger.info(
            "Job execution re-enqueued successfully due to max number of container executions."
        )

        return False

    return True


def validate_expiration(job, ex, logger):
    now = datetime.utcnow()
    unixtime = to_unix(now)

    if (
        job.metadata.get("expiration") is not None
        and job.metadata["expiration"] < unixtime
    ):
        expiration_utc = from_unix(job.metadata["expiration"])
        ex.status = JobExecution.Status.expired
        ex.error = (
            f"Job was supposed to be done before {expiration_utc.isoformat()}, "
            f"but was started at {from_unix(unixtime).isoformat()}."
        )
        ex.finished_at = now
        job.save()
        logger.info(
            "Job execution canceled due to being expired.",
            job_expiration=job.metadata["expiration"],
            current_ts=unixtime,
        )

        return False

    return True


def reenqueue_job_due_to_break(task_id, job_id, execution_id, image, command):
    args = [task_id, job_id, execution_id, image, command]
    delta = timedelta(seconds=1.0)

    future_date = to_unix(datetime.utcnow() + delta)
    enqueued = current_app.jobs_queue.enqueue_at(future_date, Categories.Job, *args)

    return enqueued


def download_image(executor, job, ex, image, tag, command, logger):
    try:
        logger.debug("Changing job status...", status=JobExecution.Status.pulling)
        ex.status = JobExecution.Status.pulling
        ex.save()
        logger.debug(
            "Job status changed successfully.", status=ex.status
        )

        logger.debug("Downloading updated container image...", image=image, tag=tag)
        before = time.time()
        executor.update_image(job.task, job, ex, image, tag)
        ellapsed = time.time() - before
        logger.info(
            "Image downloaded successfully.", image=image, tag=tag, ellapsed=ellapsed
        )
    except HostUnavailableError:
        error = traceback.format_exc()
        logger.error("Host is unavailable.", error=error)

        enqueued_id = reenqueue_job_due_to_break(
            job.task.task_id, str(job.job_id), ex.execution_id, image, command
        )

        job.metadata["enqueued_id"] = enqueued_id
        job.save()

        logger.warn("Job execution re-enqueued successfully.")

        return False
    except Exception as err:
        error = traceback.format_exc()
        logger.error("Failed to download image.", error=error)
        ex.error = error
        ex.status = JobExecution.Status.failed
        ex.save()

        current_app.report_error(
            err,
            metadata=dict(
                operation="Downloading Image",
                task_id=job.task.task_id,
                job_id=job.id,
                execution_id=ex.execution_id,
                image=image,
                tag=tag,
                command=command,
            ),
        )

        return False

    return True


def run_container(executor, job, ex, image, tag, command, logger):
    logger.debug(
        "Running command in container...", image=image, tag=tag, command=command
    )
    try:
        logger.debug("Changing job status...", status=JobExecution.Status.running)

        ex.started_at = datetime.utcnow()
        ex.status = JobExecution.Status.running
        ex.save()

        logger.debug(
            "Job status changed successfully.", status=ex.status
        )

        before = time.time()
        executor.run(job.task, job, ex, image, tag, command)
        ellapsed = time.time() - before
        logger.info(
            "Container started successfully.",
            image=image,
            tag=tag,
            command=command,
            ellapsed=ellapsed,
        )
    except HostUnavailableError:
        error = traceback.format_exc()
        logger.error("Host is unavailable.", error=error)

        enqueued_id = reenqueue_job_due_to_break(
            job.task.task_id, str(job.job_id), ex.execution_id, image, command
        )

        job.metadata["enqueued_id"] = enqueued_id
        job.save()

        logger.warn("Job execution re-enqueued successfully.")

        return False
    except Exception as err:
        error = traceback.format_exc()
        logger.error("Failed to run command", error=error)
        ex.error = error
        ex.status = JobExecution.Status.failed
        ex.save()

        current_app.report_error(
            err,
            metadata=dict(
                operation="Running Container",
                task_id=job.task.task_id,
                job_id=job.id,
                execution_id=ex.execution_id,
                image=image,
                tag=tag,
                command=command,
            ),
        )

        return False

    return True


def run_job(task_id, job_id, execution_id, image, command):
    app = current_app
    logger = app.logger.bind(
        operation="run_job",
        task_id=task_id,
        job_id=job_id,
        image=image,
        command=command,
    )

    try:
        executor = app.executor

        job = Job.get_by_id(task_id, job_id)

        if job is None:
            logger.error("Job was not found with task id and job id.")

            return False

        if not validate_max_concurrent(
            executor, task_id, job, execution_id, image, command, logger
        ):
            return False

        tag = "latest"

        if ":" in image:
            image, tag = image.split(":")

        logger = logger.bind(image=image, tag=tag)

        logger.debug("Changing job status...", status=JobExecution.Status.enqueued)
        if execution_id is None:
            ex = job.create_execution(image=image, command=command)
            ex.status = JobExecution.Status.enqueued
            ex.save()
        else:
            ex = job.get_execution_by_id(execution_id)

        logger.debug(
            "Job status changed successfully.", status=ex.status
        )
        logger = logger.bind(execution_id=ex.execution_id)
    except Exception as err:
        error = traceback.format_exc()
        logger.error("Failed to create job execution. Skipping job...", error=error)
        current_app.report_error(
            err,
            metadata=dict(task_id=task_id, job_id=job_id, image=image, command=command),
        )

        return False

    try:
        if not validate_expiration(job, ex, logger):
            return False

        logger.info("Started processing job.")

        if not download_image(executor, job, ex, image, tag, command, logger):
            return False

        if not run_container(executor, job, ex, image, tag, command, logger):
            return False

        logger.debug("Changing job status...", status=JobExecution.Status.running)
        ex.status = JobExecution.Status.running
        ex.save()
        job.save()
        logger.debug(
            "Job status changed successfully.", status=JobExecution.Status.running
        )

        current_app.monitor_queue.enqueue_in(
            "1s", Categories.Monitor, task_id, job_id, ex.execution_id
        )

        return True
    except Exception as err:
        error = traceback.format_exc()
        logger.error("Failed to run job", error=error)
        ex.status = JobExecution.Status.failed
        ex.error = "Job failed to run with error: %s" % error
        ex.save()
        job.save()

        current_app.report_error(
            err,
            metadata=dict(
                operation="Running Container",
                task_id=task_id,
                job_id=job_id,
                execution_id=ex.execution_id,
                image=image,
                tag=tag,
                command=command,
            ),
        )


def _webhook_dispatch(task, job, execution, collection, logger):
    task_id = task.task_id
    job_id = str(job.job_id)
    execution_id = str(execution.execution_id)

    for webhook in collection:
        method = "POST"
        url = webhook.get("url")

        if url is None:
            logger.warn("Webhook with empty URL found. Skipping...")

            continue
        headers = webhook.get("headers", {})
        retries = webhook.get("retries", 0)
        hook_logger = logger.bind(
            method=method, url=url, headers=headers, retries=retries, retry_count=0
        )

        hook_logger.debug("Enqueueing webhook...")
        args = [task_id, job_id, execution_id, method, url, headers, retries, 0]
        current_app.webhooks_queue.enqueue(Categories.Webhook, *args)
        hook_logger.info("Webhook enqueued successfully.")


def send_webhooks(task, job, execution, logger):
    if execution.status == JobExecution.Status.done:
        succeed = job.metadata.get("webhooks", {}).get("succeeds", [])
        logger.debug("Sending success webhooks...")
        _webhook_dispatch(task, job, execution, succeed, logger)

    if execution.status == JobExecution.Status.failed:
        fails = job.metadata.get("webhooks", {}).get("fails", [])
        logger.debug("Sending failed webhooks...")
        _webhook_dispatch(task, job, execution, fails, logger)

    finishes = job.metadata.get("webhooks", {}).get("finishes", [])
    logger.info("Sending completion webhooks...")
    _webhook_dispatch(task, job, execution, finishes, logger)


def notify_users(task, job, execution, logger):
    task_id = task.task_id
    job_id = str(job.job_id)
    execution_id = str(execution.execution_id)
    succeed = job.metadata.get("notify", {}).get("succeeds", [])
    fails = job.metadata.get("notify", {}).get("fails", [])
    finishes = job.metadata.get("notify", {}).get("finishes", [])

    if execution.status == JobExecution.Status.done:
        logger.info("Notifying users of success...")

        for email in succeed:
            logger.info("Notifying user of success...", email=email)
            subject = "Job %s/%s succeeded!" % (task_id, job_id)
            args = [task_id, job_id, execution_id, subject, email]
            current_app.notify_queue.enqueue(Categories.Notify, *args)

    if execution.status == JobExecution.Status.failed:
        logger.info("Notifying users of failure...")

        for email in fails:
            logger.info(
                "Notifying user of failure...",
                email=email,
                exit_code=execution.exit_code,
            )
            subject = "Job %s/%s failed with exit code %d!" % (
                task_id,
                job_id,
                execution.exit_code,
            )
            args = [task_id, job_id, execution_id, subject, email]
            current_app.notify_queue.enqueue(Categories.Notify, *args)

    logger.info("Notifying users of completion...")

    for email in finishes:
        logger.info(
            "Notifying user of completion...",
            email=email,
            exit_code=execution.exit_code,
        )

        subject = "Job %s/%s finished with exit code %d!" % (
            task_id,
            job_id,
            execution.exit_code,
        )
        args = [task_id, job_id, execution_id, subject, email]
        current_app.notify_queue.enqueue(Categories.Notify, *args)


def reenqueue_monitor_due_to_break(task_id, job_id, execution_id):
    args = [task_id, job_id, execution_id]
    enqueued_id = current_app.monitor_queue.enqueue_in("1s", Categories.Monitor, *args)

    return enqueued_id


def monitor_job(task_id, job_id, execution_id):
    try:
        app = current_app
        executor = app.executor

        job = Job.get_by_id(task_id, job_id)
        logger = app.logger.bind(
            operation="monitor_job",
            task_id=task_id,
            job_id=job_id,
            execution_id=execution_id,
        )

        if job is None:
            logger.error("Failed to retrieve task or job.")

            return False

        execution = job.get_execution_by_id(execution_id)

        if execution.status not in (JobExecution.Status.running,):
            logger.error("Execution result already retrieved. Skipping monitoring...")

            return False

        try:
            result = executor.get_result(job.task, job, execution)
        except HostUnavailableError as err:
            error = traceback.format_exc()
            logger.error("Failed to get results.", error=error)
            current_app.report_error(
                err,
                metadata=dict(
                    operation="Monitoring Job",
                    task_id=task_id,
                    job_id=job_id,
                    execution_id=execution_id,
                ),
            )

            reenqueue_monitor_due_to_break(task_id, job_id, execution_id)

            logger.warn("Job monitor re-enqueued successfully.")

            return False

        if result is None:
            execution.finished_at = datetime.utcnow()
            execution.exit_code = result.exit_code
            execution.status = JobExecution.Status.failed
            execution.log = ""
            execution.error = (
                "Job failed since container could not be found in docker host."
            )

            logger.debug(
                "Job failed, since container could not be found in host.",
                status="failed",
            )
            execution.save()
            job.save()

            send_webhooks(job.task, job, execution, logger)
            notify_users(job.task, job, execution, logger)

            return False

        logger.info(
            "Container result obtained.",
            container_status=result.status,
            container_exit_code=result.exit_code,
        )

        if result.status in (
            ExecutionResult.Status.created,
            ExecutionResult.Status.running,
        ):
            ellapsed = (datetime.utcnow() - execution.started_at).total_seconds()

            if ellapsed > job.metadata["timeout"]:
                execution.finished_at = datetime.utcnow()
                execution.status = JobExecution.Status.timedout
                execution.error = "Job execution timed out after %d seconds." % ellapsed

                try:
                    executor.stop_job(job.task, job, execution)
                except HostUnavailableError as err:
                    error = traceback.format_exc()
                    logger.error("Failed to stop job.", error=error)
                    current_app.report_error(
                        err,
                        metadata=dict(
                            operation="Monitoring Job",
                            task_id=task_id,
                            job_id=job_id,
                            execution_id=execution_id,
                        ),
                    )

                    reenqueue_monitor_due_to_break(task_id, job_id, execution_id)

                    logger.warn("Job monitor re-enqueued successfully.")

                    return False

                logger.debug(
                    "Job execution timed out. Storing job details in mongo db.",
                    status=execution.status,
                    ellapsed=ellapsed,
                    error=result.error,
                )
                execution.save()
                job.save()
                logger.info("Job execution timed out.", status=execution.status)

                send_webhooks(job.task, job, execution, logger)
                notify_users(job.task, job, execution, logger)

                return False

            logger.info(
                "Job has not finished. Retrying monitoring in the future.",
                container_status=result.status,
                seconds=1,
            )

            current_app.monitor_queue.enqueue_in(
                "5s", Categories.Monitor, task_id, job_id, execution_id
            )

            return True

        if (
            result.exit_code != 0
            and "retry_count" in job.metadata
            and job.metadata["retry_count"] < job.metadata["retries"]
        ):
            retry_logger = logger.bind(
                exit_code=result.exit_code,
                retry_count=job.metadata["retry_count"],
                retries=job.metadata["retries"],
            )
            retry_logger.debug("Job failed. Enqueuing job retry...")
            job.metadata["retry_count"] += 1

            new_exec = job.create_execution(execution.image, execution.command)
            new_exec.status = JobExecution.Status.enqueued

            args = [
                task_id,
                job_id,
                new_exec.execution_id,
                execution.image,
                execution.command,
            ]
            factor = app.config["EXPONENTIAL_BACKOFF_FACTOR"]
            min_backoff = app.config["EXPONENTIAL_BACKOFF_MIN_MS"] / 1000.0
            delta = timedelta(seconds=min_backoff)

            if job.metadata["retries"] > 0:
                delta = timedelta(
                    seconds=math.pow(factor, job.metadata["retry_count"]) * min_backoff
                )
            future_date = datetime.utcnow() + delta
            enqueued_id = current_app.jobs_queue.enqueue_at(
                to_unix(future_date), Categories.Job, *args
            )

            job.metadata["enqueued_id"] = enqueued_id
            job.save()

            retry_logger.info("Job execution enqueued successfully.")

            # still need to finish current execution as the retry
            # will be a new execution

        execution.finished_at = datetime.utcnow()
        execution.exit_code = result.exit_code
        execution.status = (
            JobExecution.Status.done

            if execution.exit_code == 0
            else JobExecution.Status.failed
        )
        execution.log = result.log.decode("utf-8")
        execution.error = result.error.decode("utf-8")

        logger.debug(
            "Job finished. Storing job details in mongo db.",
            status=execution.status,
            log=result.log,
            error=result.error,
        )
        execution.save()
        job.save()
        logger.info("Job details stored in mongo db.", status=execution.status)

        try:
            executor.mark_as_done(job.task, job, execution)
        except HostUnavailableError:
            error = traceback.format_exc()
            logger.error("Failed to mark job as done.", error=error)
            reenqueue_monitor_due_to_break(task_id, job_id, execution_id)

            logger.warn("Job monitor re-enqueued successfully.")

            return False

        send_webhooks(job.task, job, execution, logger)
        notify_users(job.task, job, execution, logger)

        return True
    except Exception as err:
        error = traceback.format_exc()
        logger.error("Failed to monitor job", error=error)
        current_app.report_error(
            err,
            metadata=dict(
                operation="Monitoring Job",
                task_id=task_id,
                job_id=job_id,
                execution_id=execution_id,
            ),
        )

        raise err


def send_email(task_id, job_id, execution_id, subject, to_email):
    job = Job.get_by_id(task_id, job_id)
    logger = current_app.logger.bind(
        operation="send_email",
        task_id=task_id,
        job_id=job_id,
        to_email=to_email,
        execution_id=execution_id,
        subject=subject,
    )

    if job is None:
        logger.error("Failed to retrieve task or job.")

        return False

    execution = job.get_execution_by_id(execution_id)
    logger.info("Execution loaded successfully")

    smtp_host = current_app.config["SMTP_HOST"]
    smtp_port = current_app.config["SMTP_PORT"]
    smtp_from = current_app.config["SMTP_FROM"]

    if smtp_host is None or smtp_port is None or smtp_from is None:
        logger.error(
            "SMTP_HOST, SMTP_PORT and SMTP_FROM must be configured. Skipping sending e-mail."
        )

        return False

    try:
        smtp_port = int(smtp_port)

        logger = logger.bind(smtp_host=smtp_host, smtp_port=smtp_port)

        logger.info("Connecting to SMTP Server...")
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.set_debuglevel(0)

        if current_app.config.get("SMTP_USE_SSL"):
            logger.info("Starting TLS...")
            server.starttls()

        smtp_user = current_app.config.get("SMTP_USER")
        smtp_password = current_app.config.get("SMTP_PASSWORD")

        if smtp_user and smtp_password:
            logger.info(
                "Authenticating with SMTP...",
                smtp_user=smtp_user,
                smtp_password=smtp_password,
            )
            server.login(smtp_user, smtp_password)

        from_email = current_app.config["SMTP_FROM"]

        task_url = url_for("task.get_task", task_id=task_id, _external=True)
        job_url = url_for(
            "task.get_job", task_id=task_id, job_id=job_id, _external=True
        )

        job_data = dumps(
            execution.to_dict(include_log=True, include_error=True),
            indent=4,
            sort_keys=True,
        )
        body = (
            """
Automatic message. Please do not reply to this!

Job Details:
%s
"""
            % job_data
        )

        subj = "[Fastlane] %s" % subject

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subj
        msg["From"] = from_email
        msg["To"] = to_email

        part1 = MIMEText(body, "plain")

        html_body = """<html><body>
<h2>Job Details:</h2>
<div><pre><code>%s</code></pre></div>
<div>---</div>
<p><a href="%s">[View Task Details]</a> | <a href="%s">[View Job Details]</a></p>
<div>---</div>
<p>Automatic message. Please do not reply to this!</p>
</body></html>
""" % (
            job_data,
            task_url,
            job_url,
        )
        part2 = MIMEText(html_body, "html")

        msg.attach(part1)
        msg.attach(part2)

        logger.info("Sending email...")
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        logger.info("Email sent successfully.")
    except Exception as exc:
        logger.error(
            "Sending e-mail failed with exception!", error=traceback.format_exc()
        )
        raise exc

    return True


def send_webhook(
    task_id, job_id, execution_id, method, url, headers, retries, retry_count
):
    app = current_app

    job = Job.get_by_id(task_id, job_id)
    logger = app.logger.bind(
        operation="send_webhook",
        task_id=task_id,
        job_id=job_id,
        execution_id=execution_id,
        method=method,
        url=url,
        headers=headers,
        retries=retries,
        retry_count=retry_count,
    )

    if job is None:
        logger.error("Failed to retrieve task or job.")

        return False

    execution = job.get_execution_by_id(execution_id)
    logger.info("Execution loaded successfully")

    data = execution.to_dict(include_log=True, include_error=True)
    data = loads(dumps(data))
    if "webhookDispatch" in data["metadata"]:
        del data["metadata"]["webhookDispatch"]
    data["metadata"]["custom"] = job.metadata.get("custom", {})
    data["job_id"] = job_id
    data = dumps(data)
    try:
        dispatcher = WebhooksDispatcher()
        response = dispatcher.dispatch(method, url, data, headers)

        execution.metadata.setdefault("webhookDispatch", [])
        execution.metadata["webhookDispatch"].append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "url": url,
                "statusCode": response.status_code,
                "body": response.body,
                "headers": response.headers,
            }
        )
        execution.save()
        job.save()
        logger.info("Webhook dispatched successfully.")
    except WebhooksDispatchError as err:
        error = traceback.format_exc()
        execution.metadata.setdefault("webhookDispatch", [])
        execution.metadata["webhookDispatch"].append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "url": url,
                "statusCode": err.status_code,
                "body": err.body,
                "headers": err.headers,
                "error": error,
            }
        )
        execution.metadata["webhookDispatch"] = execution.metadata["webhookDispatch"][
            -3:
        ]
        execution.save()
        job.save()

        logger.error("Failed to dispatch webhook.", err=error)
        if retry_count < retries:
            logger.debug("Retrying...")
            args = [
                task_id,
                job_id,
                execution_id,
                method,
                url,
                headers,
                retries,
                retry_count + 1,
            ]

            factor = app.config["WEBHOOKS_EXPONENTIAL_BACKOFF_FACTOR"]
            min_backoff = app.config["WEBHOOKS_EXPONENTIAL_BACKOFF_MIN_MS"] / 1000.0
            delta = to_unix(
                datetime.utcnow()
                + timedelta(seconds=math.pow(factor, retry_count) * min_backoff)
            )
            current_app.webhooks_queue.enqueue_at(delta, Categories.Webhook, *args)
            logger.info("Webhook dispatch retry scheduled.", date=delta)

    return True


def enqueue_missing_monitor_jobs(app):
    lock = app.redis.lock(
        "EnqueueMissingMonitorJobs",
        timeout=7,
        sleep=0.2,
        blocking_timeout=500,
        thread_local=False,
    )

    if not lock.acquire():
        app.logger.info(
            "Lock could not be acquired. Trying to enqueue missing monitor jobs later."
        )

        return

    try:
        # find running/created executions
        executions = Job.get_unfinished_executions(app)

        queue = app.monitor_queue

        executions_to_monitor = []
        for (job, execution) in executions:
            if "enqueued_id" in job.metadata and queue.is_scheduled(
                job.metadata["enqueued_id"]
            ):
                continue

            executions_to_monitor.append((job, execution))

        if not executions_to_monitor:
            return

        current_app.logger.info(
            "Found executions missing monitoring. Enqueueing monitor.",
            executions=len(executions_to_monitor),
        )

        # enqueue if execution not scheduled to be monitored
        for (job, execution) in executions_to_monitor:
            current_app.monitor_queue.enqueue_in(
                "5s",
                Categories.Monitor,
                job.task.task_id,
                job.job_id,
                execution.execution_id,
            )
    finally:
        try:
            lock.release()
        except Exception as err:
            current_app.logger.error("Lock release error", error=err)

