from unittest import TestCase

import pymongo
from fastapi.testclient import TestClient

from newlane.app import app


class BaseTest(TestCase):
    BASE_URL = 'http://localhost:8000'
    DATABASE = 'fastlane'

    def setUp(self):
        self.app = TestClient(app=app)

        client = pymongo.MongoClient()
        self.db = client['fastlane']

        self.db.task.delete_many({}),
        self.db.job.delete_many({}),
        self.db.execution.delete_many({})
