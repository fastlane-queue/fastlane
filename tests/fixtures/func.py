# Standard Library
import time
from subprocess import Popen

# 3rd Party
import pytest
import requests


@pytest.fixture(autouse=True)
def api():
    command = 'poetry run fastlane api -p 27356 -c ./fastlane/config/local.conf'
    runner = Popen(command.split(' '))
    time.sleep(3)
    try:
        yield
    finally:
        runner.terminate()


@pytest.fixture(autouse=True)
def worker():
    command = 'poetry run fastlane worker -c ./fastlane/config/local.conf'
    runner = Popen(command.split(' '))
    time.sleep(3)
    try:
        yield
    finally:
        runner.terminate()


class RequestClient:
    def __init__(self):
        self._client = requests.Session()

    def post(self, url, data, headers=None):
        abs_url = f"http://localhost:27356/{url.lstrip('/')}"
        response = self._client.post(
            abs_url,
            data=data,
            headers=headers,
        )
        return response.status_code, response.text, response.headers


@pytest.fixture()
def client():
    yield RequestClient()
