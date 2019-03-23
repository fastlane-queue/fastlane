# Standard Library
import datetime
from uuid import uuid4

# 3rd Party
import mongoengine.errors
from mongoengine import (
    BooleanField,
    DateTimeField,
    DictField,
    ListField,
    ReferenceField,
    StringField,
)

# Fastlane
from fastlane.models import db
from fastlane.models.categories import Categories
from fastlane.utils import words_redacted


class Job(db.Document):
    created_at = DateTimeField(required=True)
    last_modified_at = DateTimeField(required=True, default=datetime.datetime.utcnow)
    task_id = StringField(required=True)
    job_id = StringField(required=True)
    executions = ListField(ReferenceField("JobExecution"))
    task = ReferenceField(
        "Task", required=True, reverse_delete_rule=mongoengine.CASCADE
    )
    image = StringField(required=False)
    command = StringField(required=False)
    request_ip = StringField(required=False)
    metadata = DictField(required=False)
    scheduled = BooleanField(required=True, default=False)

    meta = {
        "ordering": ["-last_modified_at"],
        "indexes": ["last_modified_at", "job_id", {"fields": ["task_id", "job_id"]}],
    }

    def save(self, *args, **kwargs):
        if self.executions is None:
            self.executions = []

        if not self.created_at:
            self.created_at = datetime.datetime.utcnow()
        self.last_modified_at = datetime.datetime.utcnow()

        return super(Job, self).save(*args, **kwargs)

    def create_execution(self, image, command):
        from fastlane.models.job_execution import JobExecution

        ex_id = str(uuid4())
        ex = JobExecution(
            execution_id=ex_id,
            image=image,
            command=command,
            created_at=datetime.datetime.utcnow(),
            task=self.task,
            job=self,
        )
        ex.save()
        self.executions.append(ex)
        self.save()

        return ex

    def get_metadata(self, blacklist_fn):
        if "envs" in self.metadata:
            envs = self.metadata["envs"]
            self.metadata["envs"] = words_redacted(envs, blacklist_fn)

        return self.metadata

    def to_dict(
        self,
        include_log=False,
        include_error=False,
        include_executions=True,
        blacklist_fn=None,
    ):
        if blacklist_fn is None:
            meta = self.metadata
        else:
            meta = self.get_metadata(blacklist_fn)

        res = {
            "createdAt": self.created_at.isoformat(),
            "image": self.image,
            "command": self.command,
            "lastModifiedAt": self.last_modified_at.isoformat(),
            "taskId": self.task.task_id,
            "scheduled": self.scheduled,
            "executionCount": len(self.executions),
            "requestIPAddress": self.request_ip,
            "metadata": meta,
        }

        if include_executions:
            executions = [
                ex.to_dict(include_log, include_error)

                for ex in list(
                    reversed(sorted(self.executions, key=lambda ex: ex.created_at))
                )[:20]
            ]
            res["executions"] = executions

        return res

    @classmethod
    def get_by_id(cls, task_id, job_id):
        from fastlane.models.task import Task

        if task_id is None or task_id == "" or job_id is None or job_id == "":
            raise RuntimeError(
                "Task ID and Job ID are required and can't be None or empty."
            )

        task = Task.objects(task_id=task_id).first()
        job = cls.objects(task=task, job_id=job_id).first()

        return job

    def get_execution_by_id(self, execution_id):
        for job_execution in self.executions:
            if job_execution.execution_id == execution_id:
                return job_execution

        return None

    def get_last_execution(self):
        if not self.executions:
            return None

        return self.executions[-1]

    @classmethod
    def get_unfinished_executions(cls, app):
        from fastlane.models.job_execution import JobExecution

        query = {
            "$or": [
                {"status": JobExecution.Status.pulling},
                {"status": JobExecution.Status.running},
            ]
        }
        executions = JobExecution.objects(__raw__=query)

        execs = []

        for execution in executions:
            enqueued_id = execution.job.metadata.get("enqueued_id")

            if enqueued_id is not None and (
                app.jobs_queue.is_scheduled(enqueued_id)
                or app.jobs_queue.is_enqueued(enqueued_id)
            ):
                continue

            execs.append((execution.job, execution))

        return execs

    @classmethod
    def get_unscheduled_jobs(cls, app):
        query = {
            "$or": [
                {"metadata.startIn": {"$exists": True}},
                {"metadata.startAt": {"$exists": True}},
                {"metadata.cron": {"$exists": True}},
            ]
        }
        jobs = Job.objects(__raw__=query)

        unscheduled = []

        for job in jobs:
            if "enqueued_id" not in job.metadata:
                unscheduled.append(job)

                continue

            enqueued_id = job.metadata["enqueued_id"]

            if not app.jobs_queue.is_scheduled(
                enqueued_id
            ) and not app.jobs_queue.is_enqueued(enqueued_id):
                unscheduled.append(job)

        return list(unscheduled)

    def enqueue(self, app, execution_id, image=None, command=None):
        if image is None:
            image = self.image

        if command is None:
            command = self.command

        if image is None or command is None:
            raise RuntimeError("Can't enqueue job with no image or command.")

        logger = app.logger.bind(
            operation="enqueue_job",
            job_id=self.job_id,
            task_id=self.task.task_id,
            execution_id=execution_id,
            image=image,
            command=command,
        )

        args = [self.task.task_id, str(self.job_id), str(execution_id), image, command]

        logger.info("Job enqueued.")

        return app.jobs_queue.enqueue(Categories.Job, *args)

    def schedule_job(self, app, details):
        logger = app.logger.bind(operation="schedule_job")

        if self.image is None or self.command is None:
            logger.warn("No image or command found in job.")

            return None

        start_at = details.get("startAt", None)
        start_in = details.get("startIn", None)
        cron = details.get("cron", None)

        args = [
            str(self.task.task_id),
            str(self.job_id),
            None,
            self.image,
            self.command,
        ]

        queue_job_id = None

        if start_at is not None:
            logger.debug("Enqueuing job execution in the future...", start_at=start_at)
            enqueued_id = app.jobs_queue.enqueue_at(
                int(start_at), Categories.Job, *args
            )
            #  future_date = datetime.utcfromtimestamp(int(start_at))
            #  result = scheduler.enqueue_at(future_date, run_job, *args)
            self.metadata["enqueued_id"] = enqueued_id
            queue_job_id = enqueued_id
            self.save()
            logger.info("Job execution enqueued successfully.", start_at=start_at)
        elif start_in is not None:
            #  future_date = datetime.now(tz=timezone.utc) + start_in
            logger.debug("Enqueuing job execution in the future...", start_in=start_in)
            enqueued_id = app.jobs_queue.enqueue_in(start_in, Categories.Job, *args)
            #  result = scheduler.enqueue_at(future_date, run_job, *args)
            self.metadata["enqueued_id"] = enqueued_id
            queue_job_id = enqueued_id
            self.save()
            logger.info("Job execution enqueued successfully.", start_in=start_in)
        elif cron is not None:
            logger.debug("Enqueuing job execution using cron...", cron=cron)
            enqueued_id = app.jobs_queue.enqueue_cron(cron, Categories.Job, *args)
            self.metadata["enqueued_id"] = enqueued_id
            queue_job_id = enqueued_id
            self.metadata["cron"] = cron
            self.scheduled = True
            self.save()
            logger.info("Job execution enqueued successfully.", cron=cron)

        return queue_job_id
