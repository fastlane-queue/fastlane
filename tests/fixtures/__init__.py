# Standard Library
from os.path import abspath, dirname, join

# 3rd Party
import pytest

# Fastlane
from fastlane.api.app import Application
from fastlane.config import Config
from fastlane.models.task import Task

ROOT_CONFIG = abspath(join(dirname(__file__), "..", "testing.conf"))


@pytest.fixture
def client():
    conf = Config.load(ROOT_CONFIG)
    app = Application(conf, log_level="ERROR", testing=True)
    app.config["TESTING"] = True
    client = app.app.test_client()
    client.application.redis.flushall()

    Task.objects.delete()

    yield client
