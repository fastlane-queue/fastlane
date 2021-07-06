from unittest import mock
from unittest import IsolatedAsyncioTestCase

from newlane import core
from newlane import config


class TestCore(IsolatedAsyncioTestCase):
    def setUp(self):
        core._db = None
        core._queue = None
        core._docker = None
        core._scheduler = None

    @mock.patch('newlane.core.AIOEngine')
    @mock.patch('newlane.core.AsyncIOMotorClient')
    def test_get_db(self, client, engine):
        """ Creates db """
        core.get_db()
        self.assertIsNotNone(core._db)
        client.assert_called_once_with(config.settings.mongo)
        engine.assert_called_once_with(motor_client=client(), database='fastlane')  # noqa

    @mock.patch('newlane.core.AIOEngine')
    @mock.patch('newlane.core.AsyncIOMotorClient')
    def test_get_db_twice(self, client, engine):
        """ Creates db only once """
        core.get_db()
        core.get_db()
        self.assertIsNotNone(core._db)
        self.assertEqual(engine.call_count, 1)
        self.assertEqual(client.call_count, 1)

    @mock.patch('newlane.core.DockerClient')
    def test_get_docker(self, docker):
        """ Creates docker """
        core.get_docker()
        self.assertIsNotNone(core._docker)
        docker.assert_called_once_with(base_url=config.settings.docker)

    @mock.patch('newlane.core.DockerClient')
    def test_get_docker_twice(self, docker):
        """ Creates docker only once """
        core.get_docker()
        core.get_docker()
        self.assertEqual(docker.call_count, 1)
        self.assertIsNotNone(core._docker)

    @mock.patch('newlane.core.Redis')
    @mock.patch('newlane.core.Queue')
    def test_get_queue(self, queue, redis):
        """ Creates queue """
        core.get_queue()
        redis.assert_called_once_with(
            config.settings.redis.host,
            config.settings.redis.port
        )
        queue.assert_called_once_with(connection=redis())
        self.assertIsNotNone(core._queue)

    @mock.patch('newlane.core.Redis')
    @mock.patch('newlane.core.Queue')
    def test_get_queue_twice(self, queue, redis):
        """ Creates queue only once """
        core.get_queue()
        core.get_queue()
        self.assertEqual(redis.call_count, 1)
        self.assertEqual(queue.call_count, 1)
        self.assertIsNotNone(core._queue)

    @mock.patch('newlane.core.Redis')
    @mock.patch('newlane.core.Scheduler')
    def test_get_scheduler(self, scheduler, redis):
        """ Creates scheduler """
        core.get_scheduler()
        redis.assert_called_once_with(
            config.settings.redis.host,
            config.settings.redis.port
        )
        scheduler.assert_called_once_with(connection=redis())
        self.assertIsNotNone(core._scheduler)

    @mock.patch('newlane.core.Redis')
    @mock.patch('newlane.core.Scheduler')
    def test_get_scheduler_twice(self, scheduler, redis):
        """ Creates scheduler onle once """
        core.get_scheduler()
        core.get_scheduler()
        self.assertEqual(redis.call_count, 1)
        self.assertEqual(scheduler.call_count, 1)
        self.assertIsNotNone(core._scheduler)
