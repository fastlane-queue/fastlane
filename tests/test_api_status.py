from unittest import mock
from unittest import TestCase

from fastapi.testclient import TestClient

from newlane import app


@mock.patch('newlane.api.status.core')
class TestApiStatus(TestCase):
    def setUp(self):
        self.app = TestClient(app.app)

    def test_get_status(self, core):
        """ Gets status from services """
        core.get_docker().info.return_value = {}  # False
        core.get_queue().connection.ping.return_value = True
        core.get_db().client.server_info = mock.AsyncMock()
        core.get_db().client.server_info.return_value = {'ok': 0.0}  # False

        response = self.app.get('/status')

        self.assertEqual(response.status_code, 200)

        core.get_docker().info.assert_called_once_with()
        core.get_queue().connection.ping.assert_called_once_with()
        core.get_db().client.server_info.assert_called_once_with()
        core.get_db().client.server_info.assert_awaited()

        data = response.json()
        expected = {'redis': True, 'docker': False, 'mongo': False}
        self.assertDictEqual(data, expected)
