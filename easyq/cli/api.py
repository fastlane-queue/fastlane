from easyq.api.app import Application
from easyq.config import Config


class APIHandler:
    def __init__(self, click, host, port, config):
        self.config_path = config
        self.config = None
        self.click = click
        self.host = host
        self.port = port

        self.load_config()

    def load_config(self):
        self.click.echo(f'Loading configuration from {self.config_path}...')
        self.config = Config.load(self.config_path)

    def __call__(self):
        self.click.echo(
            f'Running easyq API at {self.host}:{self.port} in ${self.config.ENV}'
        )
        app = Application(self.config, self.host, self.port)
        app.run()
