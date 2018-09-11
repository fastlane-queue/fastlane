import time
from uuid import uuid4

from rq import Connection, Worker

from easyq.api.app import Application
from easyq.config import Config
from easyq.worker.scheduler import QueueScheduler


class WorkerHandler:
    def __init__(self, click, worker_id, jobs, monitor, config, log_level):
        self.config_path = config
        self.config = None
        self.click = click
        self.worker_id = worker_id
        self.log_level = log_level
        self.queues = []

        if jobs:
            self.queues.append('jobs')

        if monitor:
            self.queues.append('monitor')

        self.load_config()

    def load_config(self):
        # self.click.echo(f'Loading configuration from {self.config_path}...')
        self.config = Config.load(self.config_path)

    def __call__(self):
        # self.click.echo(
        # f'Running easyq worker processing queues {",".join(self.queues)}.')
        app = Application(self.config, self.log_level)
        with app.app.app_context():
            worker_kw = dict(connection=app.app.redis)

            if self.worker_id is None:
                app.logger.warn(
                    'The worker id was not set for this worker and a random one will be used.'
                )
                self.worker_id = str(uuid4())

            app.logger = app.logger.bind(
                worker_id=self.worker_id, queues=self.queues)
            app.app.logger = app.logger
            worker_kw['name'] = self.worker_id

            worker = Worker(self.queues, **worker_kw)

            schedulers = {}

            with Connection(app.app.redis):
                for queue in self.queues:
                    schedulers[queue] = QueueScheduler(queue, app=app.app)
                app.schedulers = schedulers

                # app.logger.debug('Processing enqueued items...')

                interval = 0.1

                while True:
                    for queue in self.queues:
                        # app.logger.debug(
                        # 'Processing scheduler...', queue=queue)
                        schedulers[queue].move_jobs()

                    # app.logger.debug('Processing queues...')
                    worker.work(burst=True)
                    time.sleep(interval)
