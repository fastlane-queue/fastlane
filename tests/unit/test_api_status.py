from unittest import mock
from unittest import IsolatedAsyncioTestCase

from newlane.api import status


@mock.patch('newlane.api.status.core')
class TestApiStatus(IsolatedAsyncioTestCase):
    async def test_get_status(self, core):
        """ Gets status from services """
        core.get_docker().info.return_value = {}  # False
        core.get_queue().connection.ping.return_value = True
        core.get_db().client.server_info = mock.AsyncMock()
        core.get_db().client.server_info.return_value = {'ok': 0.0}  # False

        response = await status.get_status()

        expected = {'redis': True, 'docker': False, 'mongo': False}
        self.assertDictEqual(response, expected)

        core.get_docker().info.assert_called_once_with()
        core.get_queue().connection.ping.assert_called_once_with()
        core.get_db().client.server_info.assert_called_once_with()
        core.get_db().client.server_info.assert_awaited()
