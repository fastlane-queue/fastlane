# Standard Library
import datetime

# 3rd Party
import mongoengine.errors
from mongoengine import (
    DateTimeField,
    DictField,
    IntField,
    ReferenceField,
    StringField,
)

# Fastlane
from fastlane.models import db


class JobExecution(db.Document):  # pylint: disable=no-member
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
    last_modified_at = DateTimeField(required=True, default=datetime.datetime.utcnow)
    started_at = DateTimeField(required=False)
    finished_at = DateTimeField(required=False)
    execution_id = StringField(required=True)
    image = StringField(required=True)
    command = StringField(required=True)
    request_ip = StringField(required=False)
    status = StringField(required=True, default=Status.enqueued)
    task = ReferenceField(
        "Task", required=True, reverse_delete_rule=mongoengine.CASCADE
    )
    job = ReferenceField(
        "Job", required=True, reverse_delete_rule=mongoengine.CASCADE
    )

    log = StringField(required=False)
    error = StringField(required=False)
    exit_code = IntField(required=False)
    metadata = DictField(required=False)

    def to_dict(self, include_log=False, include_error=False):
        s_at = self.started_at.isoformat() if self.started_at is not None else None
        f_at = self.finished_at.isoformat() if self.finished_at is not None else None
        res = {
            "executionId": str(self.execution_id),
            "createdAt": self.created_at.isoformat(),
            "requestIPAddress": self.request_ip,
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

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.datetime.utcnow()
        self.last_modified_at = datetime.datetime.utcnow()

        return super(JobExecution, self).save(*args, **kwargs)
