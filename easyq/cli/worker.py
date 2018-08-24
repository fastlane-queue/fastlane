from rq import Worker
from rq.local import LocalStack

from easyq.api.app import Application
from easyq.config import Config

_app = LocalStack()


class WorkerHandler:
    def __init__(self, click, worker_id, tasks, jobs, monitor, config,
                 log_level):
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

        if tasks:
            self.queues.append('tasks')

        self.load_config()

    def load_config(self):
        self.click.echo(f'Loading configuration from {self.config_path}...')
        self.config = Config.load(self.config_path)

    def __call__(self):
        self.click.echo(
            f'Running easyq worker processing queues {",".join(self.queues)}.')
        app = Application(self.config, self.log_level)
        with app.app.app_context():
            _app.push(app.app)
            worker_kw = dict(connection=app.app.redis)

            if self.worker_id is not None:
                worker_kw['name'] = self.worker_id

            worker = Worker(self.queues, **worker_kw)
            worker.work(burst=False)
