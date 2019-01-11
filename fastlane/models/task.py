# Standard Library
import datetime

# 3rd Party
import mongoengine.errors
from bson.objectid import ObjectId
from flask import url_for
from mongoengine import DateTimeField, ListField, ReferenceField, StringField

# Fastlane
from fastlane.models import db


class Task(db.Document):
    created_at = DateTimeField(required=True)
    last_modified_at = DateTimeField(required=True, default=datetime.datetime.now)
    task_id = StringField(required=True)
    jobs = ListField(ReferenceField("Job"))

    def _validate(self):
        errors = {}

        if self.task_id == "":
            errors["task_id"] = mongoengine.errors.ValidationError(
                "Field is required", field_name="task_id"
            )

        if errors:
            message = "ValidationError (%s:%s) " % (self._class_name, self.pk)
            raise mongoengine.errors.ValidationError(message, errors=errors)

    def save(self, *args, **kwargs):
        self._validate()

        if not self.created_at:
            self.created_at = datetime.datetime.now()
        self.last_modified_at = datetime.datetime.now()

        return super(Task, self).save(*args, **kwargs)

    def get_url(self):
        return url_for("task.get_task", task_id=self.task_id, _external=True)

    def to_dict(self):
        res = {
            "taskId": self.task_id,
            "createdAt": self.created_at.timestamp(),
            "lastModifiedAt": self.last_modified_at.timestamp(),
            "url": self.get_url(),
            "jobsCount": len(self.jobs),
        }

        return res

    @classmethod
    def create_task(cls, task_id):
        new_task = cls(task_id=task_id)
        new_task.save()

        return new_task

    @classmethod
    def get_tasks(cls, page=1, per_page=20):
        return cls.objects.paginate(page, per_page)  # pylint: disable=no-member

    @classmethod
    def get_by_task_id(cls, task_id):
        if task_id is None or task_id == "":
            raise RuntimeError("Task ID is required and can't be None or empty.")

        return cls.objects(task_id=task_id).no_dereference().first()

    def create_job(self):
        from fastlane.models.job import Job

        job_id = ObjectId()
        j = Job(id=job_id, job_id=str(job_id))
        j.task = self
        j.save()

        self.jobs.append(j)
        self.save()

        return j
