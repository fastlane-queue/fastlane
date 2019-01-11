"""   isort:skip_file """

# 3rd Party
from gevent import monkey

# Must be before other imports
monkey.patch_all()  # isort:skip

# Fastlane
from fastlane.api.app import Application  # NOQA pylint: disable=wrong-import-position
from fastlane.config import Config  # NOQA pylint: disable=wrong-import-position


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
