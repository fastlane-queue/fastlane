import datetime
from uuid import uuid4

import mongoengine.errors
from mongoengine import (
    BooleanField,
    DateTimeField,
    DictField,
    EmbeddedDocumentField,
    IntField,
    ListField,
    ReferenceField,
    StringField,
)

from fastlane.models import db


class JobExecution(db.EmbeddedDocument):
    class Status:
        enqueued = "enqueued"
        pulling = "pulling"
        running = "running"
        done = "done"
        failed = "failed"
        timedout = "timedout"
        expired = "expired"
        stopped = "stopped"

    created_at = DateTimeField(required=True)
    started_at = DateTimeField(required=False)
    finished_at = DateTimeField(required=False)
    execution_id = StringField(required=True)
    image = StringField(required=True)
    command = StringField(required=True)
    status = StringField(required=True, default=Status.enqueued)

    log = StringField(required=False)
    error = StringField(required=False)
    exit_code = IntField(required=False)
    metadata = DictField(required=False)

    def to_dict(self, include_log=False, include_error=False):
        s_at = self.started_at.isoformat() if self.started_at is not None else None
        f_at = self.finished_at.isoformat() if self.finished_at is not None else None
        res = {
            "createdAt": self.created_at.isoformat(),
            "startedAt": s_at,
            "finishedAt": f_at,
            "image": self.image,
            "command": self.command,
            "metadata": self.metadata,
            "status": self.status,
            "exitCode": self.exit_code,
        }

        if self.finished_at is not None:
            res["finishedAt"] = self.finished_at.isoformat()

        if include_log:
            res["log"] = self.log

        if include_error:
            res["error"] = self.error

        return res


class Job(db.Document):
    created_at = DateTimeField(required=True)
    last_modified_at = DateTimeField(required=True, default=datetime.datetime.now)
    job_id = StringField(required=True)
    executions = ListField(EmbeddedDocumentField(JobExecution))
    task = ReferenceField(
        "Task", required=True, reverse_delete_rule=mongoengine.CASCADE
    )
    metadata = DictField(required=False)
    scheduled = BooleanField(required=True, default=False)

    def save(self, *args, **kwargs):
        if self.executions is None:
            self.executions = []

        if not self.created_at:
            self.created_at = datetime.datetime.utcnow()
        self.last_modified_at = datetime.datetime.utcnow()

        return super(Job, self).save(*args, **kwargs)

    def create_execution(self, image, command):
        ex_id = str(uuid4())
        ex = JobExecution(
            execution_id=ex_id,
            image=image,
            command=command,
            created_at=datetime.datetime.utcnow(),
        )
        self.executions.append(ex)
        self.save()

        return ex

    def get_metadata(self, blacklist):
        if "envs" in self.metadata:
            envs = {}

            for key, val in self.metadata["envs"].items():
                if key.lower() in blacklist:
                    envs[key] = "*" * len(str(val))
                else:
                    envs[key] = val

            self.metadata["envs"] = envs

        return self.metadata

    def to_dict(
        self,
        include_log=False,
        include_error=False,
        include_executions=True,
        blacklist=None,
    ):
        if blacklist is None:
            blacklist = []

        meta = self.get_metadata(blacklist)

        res = {
            "createdAt": self.created_at.isoformat(),
            "lastModifiedAt": self.last_modified_at.isoformat(),
            "taskId": self.task.task_id,
            "scheduled": self.scheduled,
            "executionCount": len(self.executions),
            "metadata": meta,
        }

        if include_executions:
            executions = [
                ex.to_dict(include_log, include_error) for ex in self.executions
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

        t = Task.objects(task_id=task_id).first()
        j = cls.objects(task=t, job_id=job_id).first()

        return j

    def get_execution_by_id(self, execution_id):
        for job_execution in self.executions:
            if job_execution.execution_id == execution_id:
                return job_execution

        return None
