import datetime

from mongoengine import DateTimeField, StringField

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
    container_id = StringField(required=False)
    status = StringField(required=True, default=Status.enqueued)

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.datetime.now()
        self.last_modified_at = datetime.datetime.now()

        return super(Job, self).save(*args, **kwargs)

    @classmethod
    def create_job(cls, job_id):
        j = cls(job_id=job_id, status=Job.Status.enqueued)
        j.save()

        return j
