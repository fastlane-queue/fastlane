import datetime

import mongoengine.errors
from mongoengine import DateTimeField, ReferenceField, StringField

from easyq.models import db


class Job(db.Document):
    class Status:
        enqueued = 'enqueued'
        pulling = 'pulling'
        running = 'running'
        done = 'done'
        failed = 'failed'

    created_at = DateTimeField(required=True)
    last_modified_at = DateTimeField(
        required=True, default=datetime.datetime.now)
    job_id = StringField(required=True)
    image = StringField(required=True)
    command = StringField(required=True)
    container_id = StringField(required=False)
    status = StringField(required=True, default=Status.enqueued)
    task = ReferenceField(
        'Task', required=True, reverse_delete_rule=mongoengine.CASCADE)

    log = StringField(required=False)
    error = StringField(required=False)

    def _validate(self):
        errors = {}

        if self.image == "":
            errors["image"] = mongoengine.errors.ValidationError(
                'Field is required', field_name="image")

        if self.command == "":
            errors["command"] = mongoengine.errors.ValidationError(
                'Field is required', field_name="command")

        if errors:
            message = 'ValidationError (%s:%s) ' % (self._class_name, self.pk)
            raise mongoengine.errors.ValidationError(message, errors=errors)

    def save(self, *args, **kwargs):
        self._validate()

        if not self.created_at:
            self.created_at = datetime.datetime.now()
        self.last_modified_at = datetime.datetime.now()

        return super(Job, self).save(*args, **kwargs)

    def to_dict(self, include_log=False, include_error=False):
        res = {
            'createdAt': self.created_at.isoformat(),
            'lastModifiedAt': self.last_modified_at.isoformat(),
            'image': self.image,
            'command': self.command,
            'containerId': self.container_id,
            'status': self.status,
        }

        if include_log:
            res['log'] = self.log

        if include_error:
            res['error'] = self.error

        return res

    @classmethod
    def get_by_id(cls, task_id, job_id):
        from easyq.models.task import Task

        if task_id is None or task_id == "" or job_id is None or job_id == "":
            raise RuntimeError(
                "Task ID and Job ID are required and can't be None or empty.")

        t = Task.objects(task_id=task_id).first()
        j = cls.objects(task=t, job_id=job_id).first()

        return j
