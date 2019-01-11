# 3rd Party
from flask import Blueprint
from rq import Queue
from rq_scheduler import Scheduler

bp = Blueprint("rq", __name__)  # pylint: disable=invalid-name


class JobQueue:
    def __init__(self, queue_name, app):
        self.app = app
        self.queue_name = queue_name
        self._queue = None
        self._scheduler = None

    def enqueue_in(self, *args, **kw):
        self.app.logger.info("Scheduling execution for the future.", **kw)

        return self._scheduler.enqueue_in(*args, **kw)

    def enqueue_at(self, *args, **kw):
        self.app.logger.info("Scheduling execution for a specific timestamp.", **kw)

        return self._scheduler.enqueue_at(*args, **kw)

    def enqueue(self, *args, **kw):
        return self.queue.enqueue(*args, **kw)

    @property
    def queue(self):
        if self._queue is None:
            self._queue = Queue(self.queue_name, connection=self.app.redis)

        return self._queue

    @property
    def scheduler(self):
        if self._scheduler is None:
            self._scheduler = Scheduler(queue=self._queue)

        return self._scheduler


def init_app(app):
    for queue_name in ["jobs", "monitor", "notify", "webhooks"]:
        key = queue_name.rstrip("s")
        setattr(app, "%s_queue" % key, JobQueue(queue_name, app))
