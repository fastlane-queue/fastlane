from rq_scheduler import Scheduler


class QueueScheduler:
    def __init__(self, queue_name, app):
        self.app = app
        self.logger = self.app.logger.bind(queue_name=queue_name)
        self.scheduler = Scheduler(queue_name=queue_name, connection=app.redis)

    def move_jobs(self):
        if self.scheduler.acquire_lock():
            try:
                jobs = self.scheduler.get_jobs()
                self.logger.debug(
                    "Lock acquired. Enqueuing scheduled jobs...", jobs=jobs
                )
                self.scheduler.enqueue_jobs()
            finally:
                self.scheduler.remove_lock()
        else:
            self.logger.debug(
                "Lock could not be acquired. Enqueuing scheduled jobs skipped. Trying again next cycle."
            )
