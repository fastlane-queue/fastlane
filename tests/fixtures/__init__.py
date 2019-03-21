# Standard Library
from os.path import abspath, dirname, join
from uuid import uuid4

# 3rd Party
import pytest

# Fastlane
from fastlane.api.app import Application
from fastlane.cli.worker import WorkerHandler
from fastlane.config import Config
from fastlane.models.job import Job
from fastlane.models.task import Task

ROOT_CONFIG = abspath(join(dirname(__file__), "..", "testing.conf"))


@pytest.fixture
def client():
    conf = Config.load(ROOT_CONFIG)
    app = Application(conf, log_level="ERROR", testing=True)
    app.config["TESTING"] = True
    cli = app.app.test_client()
    cli.application.redis.flushall()

    Task.objects.delete()
    Job.objects.delete()

    yield cli


@pytest.fixture
def auth_client():
    conf = Config.load(ROOT_CONFIG)
    conf.BASIC_AUTH_USERNAME = "test"
    conf.BASIC_AUTH_PASSWORD = "auth"
    app = Application(conf, log_level="ERROR", testing=True)
    app.config["TESTING"] = True
    cli = app.app.test_client()
    cli.application.redis.flushall()

    Task.objects.delete()
    Job.objects.delete()

    yield cli


@pytest.fixture
def worker():
    conf = Config.load(ROOT_CONFIG)
    app = Application(conf, log_level="ERROR", testing=True)
    app.config["TESTING"] = True
    cli = app.app.test_client()
    cli.application.redis.flushall()

    Task.objects.delete()
    Job.objects.delete()

    worker_instance = WorkerHandler(
        None, str(uuid4()), True, True, True, True, app.config, 0, app=app
    )

    yield worker_instance
