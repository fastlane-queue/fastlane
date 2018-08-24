import datetime

import mongoengine.errors
from mongoengine import DateTimeField, StringField

from easyq.models import db


class Job(db.EmbeddedDocument):
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
