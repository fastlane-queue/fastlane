# Fastlane
from fastlane.api.app import Application
from fastlane.config import Config


class PruneHandler:
    def __init__(self, click, config, log_level):
        self.config_path = config
        self.config = None
        self.click = click
        self.log_level = log_level

        self.load_config()

    def load_config(self):
        self.config = Config.load(self.config_path)

    def __call__(self):
        app = Application(self.config, self.log_level).app
        app.logger.info(f"Running fastlane prune...")
        with app.app_context():
            removed = app.executor.remove_done()
            app.logger.info(f"Prune done.", removed=removed)
