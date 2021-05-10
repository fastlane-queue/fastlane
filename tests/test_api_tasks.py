from unittest import mock
from unittest import TestCase

from fastapi import HTTPException
from fastapi.testclient import TestClient

from newlane import app
from newlane import core
from newlane import crud


class TestApiTasks(TestCase):
    def setUp(self):
        self.crud_patch = mock.patch('newlane.api.tasks.crud')

        self.crud = self.crud_patch.start()

        self.crud.task = mock.Mock()
        self.crud.task.page = mock.AsyncMock()
        self.crud.task.get_or_404 = mock.AsyncMock()
        self.crud.task.get_or_create = mock.AsyncMock()

        self.app = TestClient(app.app)

    def tearDown(self):
        self.crud_patch.stop()

    def test_post_task(self):
        """ Posts task """
        self.crud.task.get_or_create.return_value = {}

        body = {'name': 'nice'}
        response = self.app.post('/tasks/', json=body)

        self.assertEqual(response.status_code, 200)

        self.crud.task.get_or_create.assert_called_once_with(name='nice')
        self.crud.task.get_or_create.assert_awaited()

    def test_get_task(self):
        """ Gets task """
        self.crud.task.get_or_404.return_value = {}

        response = self.app.get('/tasks/nice')

        self.assertEqual(response.status_code, 200)

        self.crud.task.get_or_404.assert_called_once_with(name='nice')
        self.crud.task.get_or_404.assert_awaited()

    def test_get_task_404(self):
        """ Gets task, 404 """
        self.crud.task.get_or_404.side_effect = HTTPException(404)

        response = self.app.get('/tasks/nice')

        self.assertEqual(response.status_code, 404)

        self.crud.task.get_or_404.assert_called_once_with(name='nice')
        self.crud.task.get_or_404.assert_awaited()

    def test_get_tasks(self):
        """ Gets tasks """
        self.crud.task.page.return_value = {}

        params = {'page': 7, 'size': 4}
        response = self.app.get('/tasks', params=params)

        self.assertEqual(response.status_code, 200)

        self.crud.task.page.assert_called_once_with(page=7, size=4)
        self.crud.task.page.assert_awaited()
