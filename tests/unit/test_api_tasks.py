from unittest import mock
from unittest import IsolatedAsyncioTestCase

from fastapi import HTTPException

from newlane.api import tasks
from newlane.api import payloads


@mock.patch('newlane.api.tasks.crud', autospec=True)
class TestApiTasks(IsolatedAsyncioTestCase):
    async def test_post_task(self, crud):
        """ Posts task """
        crud.task.get_or_create.return_value = {}

        data = payloads.Task(name='nice')
        response = await tasks.post_task(data)

        self.assertDictEqual(response, {})

        crud.task.get_or_create.assert_called_once_with(name='nice')
        crud.task.get_or_create.assert_awaited()

    async def test_get_task(self, crud):
        """ Gets task """
        crud.task.get_or_404.return_value = {}

        response = await tasks.get_task('nice')

        self.assertDictEqual(response, {})

        crud.task.get_or_404.assert_called_once_with(name='nice')
        crud.task.get_or_404.assert_awaited()

    async def test_get_task_404(self, crud):
        """ Gets task, 404 """
        crud.task.get_or_404.side_effect = HTTPException(404)

        with self.assertRaises(HTTPException):
            await tasks.get_task('nice')

        crud.task.get_or_404.assert_called_once_with(name='nice')
        crud.task.get_or_404.assert_awaited()

    async def test_get_tasks(self, crud):
        """ Gets tasks """
        crud.task.page.return_value = {}

        response = await tasks.get_tasks(page=7, size=4)

        self.assertDictEqual(response, {})

        crud.task.page.assert_called_once_with(page=7, size=4)
        crud.task.page.assert_awaited()
