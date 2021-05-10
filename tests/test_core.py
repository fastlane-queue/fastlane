from unittest import mock
from unittest import IsolatedAsyncioTestCase

from newlane import core
from newlane import config

class TestCore(IsolatedAsyncioTestCase):
    def setUp(self):
        # db
        core._db = None
        core.AIOEngine = mock.Mock()
        core.AsyncIOMotorClient = mock.Mock()

        # docker
        core._docker = None
        core.DockerClient = mock.Mock()

        # queue
        core._queue = None
        core.Redis = mock.Mock()
        core.Queue = mock.Mock()

        # scheduler
        core._scheduler = None
        core.Scheduler = mock.Mock()

    def test_get_db(self):
        """ Creates db """
        core.get_db()
        core.AsyncIOMotorClient.assert_called_once_with(config.settings.mongo)
        core.AIOEngine.assert_called_once_with(
            motor_client=core.AsyncIOMotorClient(),
            database='fastlane'
        )
        self.assertIsNotNone(core._db)

    def test_get_db_twice(self):
        """ Creates db only once """
        core.get_db()
        core.get_db()
        self.assertEqual(core.AIOEngine.call_count, 1)
        self.assertEqual(core.AsyncIOMotorClient.call_count, 1)
        self.assertIsNotNone(core._db)

    def test_get_docker(self):
        """ Creates docker """
        core.get_docker()
        core.DockerClient\
            .assert_called_once_with(base_url=config.settings.docker)
        self.assertIsNotNone(core._docker)
    
    def test_get_docker_twice(self):
        """ Creates docker only once """
        core.get_docker()
        core.get_docker()
        self.assertEqual(core.DockerClient.call_count, 1)
        self.assertIsNotNone(core._docker)

    def test_get_queue(self):
        """ Creates queue """
        core.get_queue()
        core.Redis.assert_called_once_with(
            config.settings.redis.host, 
            config.settings.redis.port
        )
        core.Queue.assert_called_once_with(connection=core.Redis())
        self.assertIsNotNone(core._queue)

    def test_get_queue_twice(self):
        """ Creates queue only once """
        core.get_queue()
        core.get_queue()
        self.assertEqual(core.Redis.call_count, 1)
        self.assertEqual(core.Queue.call_count, 1)
        self.assertIsNotNone(core._queue)
    
    def test_get_scheduler(self):
        """ Creates scheduler """
        core.get_scheduler()
        core.Redis.assert_called_once_with(
            config.settings.redis.host, 
            config.settings.redis.port
        )
        core.Scheduler.assert_called_once_with(connection=core.Redis())
        self.assertIsNotNone(core._scheduler)
    
    def test_get_scheduler_twice(self):
        """ Creates scheduler onle once """
        core.get_scheduler()
        core.get_scheduler()
        self.assertEqual(core.Redis.call_count, 1)
        self.assertEqual(core.Scheduler.call_count, 1)
        self.assertIsNotNone(core._scheduler)
