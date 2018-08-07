from easyq.config import Config


class APIHandler:
    def __init__(self, click, config):
        self.config_path = config
        self.config = None
        self.click = click

        self.load_config()

    def load_config(self):
        self.click.echo(f'Loading configuration from {self.config_path}...')
        self.config = Config.load(self.config_path)

    def __call__(self):
        pass
