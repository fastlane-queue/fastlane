# Standard Library
import time
import traceback
from uuid import uuid4

# Fastlane
from fastlane.api.app import Application
from fastlane.config import Config
from fastlane.models.categories import QueueNames
from fastlane.worker.job import enqueue_missing_monitor_jobs


class WorkerHandler:
    def __init__(
        self,
        click,
        worker_id,
        jobs,
        monitor,
        notify,
        webhooks,
        config,
        log_level,
        app=None,
    ):
        if isinstance(config, (str, bytes)):
            self.config_path = config
            self.config = None
        else:
            self.config_path = None
            self.config = config

        self.click = click
        self.worker_id = worker_id
        self.log_level = log_level
        self.queues = set()

        if jobs:
            self.queues.add(QueueNames.Job)

        if monitor:
            self.queues.add(QueueNames.Monitor)

        if notify:
            self.queues.add(QueueNames.Notify)

        if webhooks:
            self.queues.add(QueueNames.Webhook)

        self.load_config()
        self.app = app
        self.queue_group = None
        self.last_verified_missing_jobs = time.time()

        if self.app is not None:
            self.queue_group = self.app.app.queue_group

    def load_config(self):
        # self.click.echo(f'Loading configuration from {self.config_path}...')

        if self.config is None:
            self.config = Config.load(self.config_path)

    def loop_once(self):
        self.queue_group.move_jobs()

        if time.time() - self.last_verified_missing_jobs > 10:
            try:
                enqueue_missing_monitor_jobs(self.app.app)
            finally:
                self.last_verified_missing_jobs = time.time()

        item = self.queue_group.dequeue(queues=self.queues, timeout=5)

        if item is None:
            return None

        return item.run()

    def __call__(self):
        # self.click.echo(
        # f'Running fastlane worker processing queues {",".join(self.queues)}.')
        self.app = app = Application(self.config, self.log_level)
        self.queue_group = self.app.app.queue_group

        app.logger.info(
            f'Running fastlane worker processing queues {",".join(self.queues)}.'
        )
        interval = app.config["WORKER_SLEEP_TIME_MS"] / 1000.0
        self.last_verified_missing_jobs = time.time()

        with app.app.app_context():
            if self.worker_id is None:
                app.logger.warn(
                    "The worker id was not set for this worker and a random one will be used."
                )
                self.worker_id = str(uuid4())

            app.logger = app.logger.bind(worker_id=self.worker_id, queues=self.queues)
            app.app.logger = app.logger

            while True:
                try:
                    self.loop_once()
                    time.sleep(interval)
                except Exception:
                    error = traceback.format_exc()
                    app.logger.error("Failed to process job.", error=error)
