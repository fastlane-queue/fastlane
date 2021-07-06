from unittest import mock
from unittest import IsolatedAsyncioTestCase

from newlane.api import docker


@mock.patch('newlane.api.docker.core')
class TestApiDocker(IsolatedAsyncioTestCase):
    async def test_get_containers(self, core):
        """ Gets containers """
        core.get_docker().containers.list.return_value = [1, 2, 3]

        response = await docker.get_containers()
        self.assertListEqual(response, [1, 2, 3])

        core.get_docker().containers.list.assert_called_once_with()

    async def test_post_prune(self, core):
        """ Posts prune """
        core.get_docker().containers.prune.return_value = {'nice': 123}

        response = await docker.post_prune()
        self.assertDictEqual(response, {'nice': 123})

        core.get_docker().containers.prune.assert_called_once_with()
