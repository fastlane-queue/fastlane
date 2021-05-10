from unittest import mock
from unittest import TestCase

from fastapi import HTTPException
from fastapi.testclient import TestClient

from newlane import app
from newlane import core
from newlane import crud
from newlane import worker


class TestApiTasks(TestCase):
    def setUp(self):
        crud.task = mock.Mock()
        crud.task.page = mock.AsyncMock()
        crud.task.get_or_404 = mock.AsyncMock()
        crud.task.get_or_create = mock.AsyncMock()
        self.app = TestClient(app.app)

    def test_post_task(self):
        """ Posts task """
        crud.task.get_or_create.return_value = {}

        body = {'name': 'nice'}
        response = self.app.post('/tasks/', json=body)

        self.assertEqual(response.status_code, 200)

        crud.task.get_or_create.assert_called_once_with(name='nice')
        crud.task.get_or_create.assert_awaited()

    def test_get_task(self):
        """ Gets task """
        crud.task.get_or_404.return_value = {}

        response = self.app.get('/tasks/nice')

        self.assertEqual(response.status_code, 200)

        crud.task.get_or_404.assert_called_once_with(name='nice')
        crud.task.get_or_404.assert_awaited()

    def test_get_task_404(self):
        """ Gets task, 404 """
        crud.task.get_or_404.side_effect = HTTPException(404)

        response = self.app.get('/tasks/nice')

        self.assertEqual(response.status_code, 404)

        crud.task.get_or_404.assert_called_once_with(name='nice')
        crud.task.get_or_404.assert_awaited()

    def test_get_tasks(self):
        """ Gets tasks """
        crud.task.page.return_value = {}

        params = {'page': 7, 'size': 4}
        response = self.app.get('/tasks', params=params)

        self.assertEqual(response.status_code, 200)

        crud.task.page.assert_called_once_with(page=7, size=4)
        crud.task.page.assert_awaited()