from unittest import mock
from unittest import TestCase

from fastapi.testclient import TestClient

from newlane import app


@mock.patch('newlane.api.docker.core')
class TestApiDocker(TestCase):
    def setUp(self):
        self.app = TestClient(app.app)

    def test_get_containers(self, core):
        """ Gets containers """
        core.get_docker().containers.list.return_value = [1, 2, 3]

        response = self.app.get('/docker/containers')

        self.assertEqual(response.status_code, 200)

        core.get_docker().containers.list.assert_called_once_with()

        data = response.json()
        self.assertListEqual(data, [1, 2, 3])

    def test_post_prune(self, core):
        """ Posts prune """
        core.get_docker().containers.prune.return_value = {'nice': 123}

        response = self.app.post('/docker/prune')

        self.assertEqual(response.status_code, 200)

        core.get_docker().containers.prune.assert_called_once_with()

        data = response.json()
        self.assertDictEqual(data, {'nice': 123})
