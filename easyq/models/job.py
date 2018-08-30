import datetime

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
    log = StringField(required=False)
    error = StringField(required=False)

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
