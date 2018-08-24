import datetime
from uuid import uuid4

import mongoengine.errors
from mongoengine import (BooleanField, DateTimeField, EmbeddedDocumentField,
                         ListField, StringField)

from easyq.models import db
from easyq.models.job import Job


class Task(db.Document):
    created_at = DateTimeField(required=True)
    last_modified_at = DateTimeField(
        required=True, default=datetime.datetime.now)
    task_id = StringField(required=True)
    done = BooleanField(required=True, default=False)
    jobs = ListField(EmbeddedDocumentField(Job))
    pattern = StringField(required=False)
    image = StringField(required=True)
    command = StringField(required=True)

    def _validate(self):
        errors = {}

        if self.task_id == "":
            errors["task_id"] = mongoengine.errors.ValidationError(
                'Field is required', field_name="task_id")

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

        return super(Task, self).save(*args, **kwargs)

    @classmethod
    def create_task(cls, task_id, image, command):
        t = cls(task_id=task_id, image=image, command=command, done=False)
        t.save()

        return t

    @classmethod
    def get_by_task_id(cls, task_id):
        if task_id is None or task_id == "":
            raise RuntimeError(
                "Task ID is required and can't be None or empty.")

        t = cls.objects(task_id=task_id).first()

        return t

    def create_job(self, job_id):
        j = Job(
            job_id=job_id,
            status=Job.Status.enqueued,
            image=self.image,
            command=self.command,
        )

        if not j.created_at:
            j.created_at = datetime.datetime.now()
        j.last_modified_at = datetime.datetime.now()
        self.jobs.append(j)
        self.save()

        return j

    def get_job_by_job_id(self, job_id):
        for job in self.jobs:
            if job.job_id == job_id:
                return job

        return None
