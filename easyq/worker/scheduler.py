from rq_scheduler import Scheduler


class QueueScheduler:
    def __init__(self, queue_name, app):
        self.scheduler = Scheduler(queue_name=queue_name, connection=app.redis)

    def move_jobs(self):
        if self.scheduler.acquire_lock():
            try:
                self.scheduler.enqueue_jobs()
            finally:
                self.scheduler.remove_lock()
