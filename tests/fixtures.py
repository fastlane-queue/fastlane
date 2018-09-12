from os.path import abspath, dirname, join

import pytest

from easyq.api.app import Application
from easyq.config import Config
from easyq.models.task import Task

ROOT_CONFIG = abspath(join(dirname(__file__), 'testing.conf'))


@pytest.fixture
def client():
    conf = Config.load(ROOT_CONFIG)
    app = Application(conf, log_level='ERROR', testing=True)
    app.config['TESTING'] = True
    client = app.app.test_client()
    client.application.redis.flushall()

    Task.objects.delete()

    yield client