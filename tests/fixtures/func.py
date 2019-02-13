import time
from json import loads

# 3rd Party
import pytest
import requests
from pymongo import MongoClient
from preggy import assertion


@pytest.fixture(autouse=True)
def cleanup():
    mongo_client = MongoClient("localhost", 27355)
    database = mongo_client.fastlane_test
    database.Task.drop()
    database.Job.drop()

    yield


class RequestClient:
    def __init__(self):
        self._client = requests.Session()

    def get(self, url, headers=None, absolute=False):
        abs_url = url

        if not absolute:
            abs_url = f"http://localhost:10000/{url.lstrip('/')}"
        response = self._client.get(abs_url, headers=headers)

        return response.status_code, response.text, response.headers

    def post(self, url, data, headers=None, absolute=False):
        abs_url = url

        if not absolute:
            abs_url = f"http://localhost:10000/{url.lstrip('/')}"
        response = self._client.post(abs_url, json=data, headers=headers)

        return response.status_code, response.text, response.headers


@pytest.fixture()
def client():
    yield RequestClient()


@assertion
def to_have_finished_with(topic, cli, timeout=10, **kw):
    def validate(execution, **arguments):
        for key, value in arguments.items():
            val = execution[key]
            if isinstance(val, (bytes, str)):
                val = val.strip()
            if val != value:
                raise AssertionError(
                    'Execution did not match expectations! \n'
                    f'{key}:\n\tExpected: {value}\n\tActual:   {val}')

    start = time.time()

    last_obj = None
    while time.time() - start < timeout:
        status_code, body, _ = cli.get(topic, absolute=True)

        if status_code != 200:
            raise AssertionError(
                f"{topic} could not be found (status: {status_code}).")

        last_obj = loads(body)

        try:
            if validate(last_obj['execution'], **kw):
                return
        except AssertionError:
            pass

        time.sleep(0.5)

    validate(last_obj['execution'], **kw)
