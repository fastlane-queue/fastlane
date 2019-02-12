# 3rd Party
import pytest
import requests
from pymongo import MongoClient


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
