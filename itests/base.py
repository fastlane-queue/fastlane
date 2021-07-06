from unittest import TestCase

import pymongo
from fastapi.testclient import TestClient

from newlane.app import app


class BaseTest(TestCase):
    DATABASE = 'fastlane'

    def setUp(self):
        super().setUp()
        self.app = TestClient(app=app)

        client = pymongo.MongoClient()
        self.db = client[self.DATABASE]

        self.db.execution.delete_many({})
        self.db.job.delete_many({})
        self.db.task.delete_many({})
