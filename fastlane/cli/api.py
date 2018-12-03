from fastlane.api.app import Application
from fastlane.config import Config


class APIHandler:
    def __init__(self, click, host, port, config, log_level):
        self.config_path = config
        self.config = None
        self.click = click
        self.host = host
        self.port = port
        self.log_level = log_level

        self.load_config()

    def load_config(self):
        # self.click.echo(f'Loading configuration from {self.config_path}...')
        self.config = Config.load(self.config_path)

    def __call__(self):
        app = Application(self.config, self.log_level)
        app.logger.info(
            "fastlane is runnning.",
            host=self.host,
            port=self.port,
            environment=self.config.ENV,
        )
        app.run(self.host, self.port)
