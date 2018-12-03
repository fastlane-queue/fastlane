import datetime

import mongoengine.errors
from bson.objectid import ObjectId
from mongoengine import (BooleanField, DateTimeField, ListField,
                         ReferenceField, StringField)

from fastlane.models import db


class Task(db.Document):
    created_at = DateTimeField(required=True)
    last_modified_at = DateTimeField(
        required=True, default=datetime.datetime.now)
    task_id = StringField(required=True)
    jobs = ListField(ReferenceField('Job'))

    def _validate(self):
        errors = {}

        if self.task_id == "":
            errors["task_id"] = mongoengine.errors.ValidationError(
                'Field is required', field_name="task_id")

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
    def create_task(cls, task_id):
        t = cls(task_id=task_id)
        t.save()

        return t

    @classmethod
    def get_by_task_id(cls, task_id):
        if task_id is None or task_id == "":
            raise RuntimeError(
                "Task ID is required and can't be None or empty.")

        t = cls.objects(task_id=task_id).no_dereference().first()

        return t

    def create_job(self):
        from fastlane.models.job import Job

        job_id = ObjectId()
        j = Job(
            id=job_id,
            job_id=str(job_id),
        )
        j.task = self
        j.save()

        self.jobs.append(j)
        self.save()

        return j
