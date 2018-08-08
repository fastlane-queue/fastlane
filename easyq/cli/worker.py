from rq import Worker

from easyq.api.app import Application
from easyq.config import Config


class WorkerHandler:
    def __init__(self, click, worker_id, jobs, monitor, config):
        self.config_path = config
        self.config = None
        self.click = click
        self.worker_id = worker_id
        self.queues = []

        if jobs:
            self.queues.append('jobs')

        if monitor:
            self.queues.append('monitor')

        self.load_config()

    def load_config(self):
        self.click.echo(f'Loading configuration from {self.config_path}...')
        self.config = Config.load(self.config_path)

    def __call__(self):
        self.click.echo(
            f'Running easyq worker processing queues {",".join(self.queues)}.')
        app = Application(self.config)
        with app.app.app_context():
            worker_kw = dict(connection=app.app.redis)

            if self.worker_id is not None:
                worker_kw['name'] = self.worker_id

            worker = Worker(self.queues, **worker_kw)
            worker.work(burst=False)
