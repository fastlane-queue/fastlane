import uuid
from unittest import mock
from unittest import TestCase
from datetime import timedelta

from fastapi import HTTPException
from fastapi.testclient import TestClient

from newlane import app
from newlane import core
from newlane import crud


class TestApiExecutions(TestCase):
    def setUp(self):
        self.core_patch = mock.patch('newlane.api.executions.core')
        self.crud_patch = mock.patch('newlane.api.executions.crud')

        self.core = self.core_patch.start()
        self.crud = self.crud_patch.start()

        self.crud.task.get_or_404 = mock.AsyncMock()
        self.crud.job.get_or_404 = mock.AsyncMock()
        self.crud.execution.create = mock.AsyncMock()
        self.crud.execution.save = mock.AsyncMock()
        self.crud.execution.get_or_404 = mock.AsyncMock()
        self.crud.execution.page = mock.AsyncMock()

        self.app = TestClient(app.app)

    def tearDown(self):
        self.core_patch.stop()
        self.crud_patch.stop()

    def test_post_execution(self):
        """ Posts execution """
        self.crud.execution.save.return_value = {}

        job = uuid.uuid4()
        response = self.app.post(f'/tasks/nice/jobs/{job}/executions/')

        self.assertEqual(response.status_code, 200)

        self.crud.task.get_or_404.assert_called_once_with(name='nice')
        self.crud.task.get_or_404.assert_awaited()
        self.crud.job.get_or_404.assert_called_once_with(task=mock.ANY, id=job)
        self.crud.job.get_or_404.assert_awaited()
        self.core.get_queue.assert_called_once_with()
        self.core.get_queue().enqueue\
            .assert_called_once_with(mock.ANY, mock.ANY)
        self.crud.execution.save.assert_called_once_with(mock.ANY)
        self.crud.execution.save.assert_awaited()

    def test_get_execution(self):
        """ Gets execution """
        self.crud.execution.get_or_404.return_value = {}

        job = uuid.uuid4()
        uid = uuid.uuid4()
        response = self.app.get(f'/tasks/nice/jobs/{job}/executions/{uid}')

        self.assertEqual(response.status_code, 200)

        self.crud.execution.get_or_404\
            .assert_called_once_with(job=mock.ANY, id=uid)
        self.crud.execution.get_or_404.assert_awaited()

    def test_get_execution_404(self):
        """ Gets execution, 404 """
        self.crud.execution.get_or_404.side_effect = HTTPException(404)

        job = uuid.uuid4()
        uid = uuid.uuid4()
        response = self.app.get(f'/tasks/nice/jobs/{job}/executions/{uid}')

        self.assertEqual(response.status_code, 404)

        self.crud.execution.get_or_404\
            .assert_called_once_with(job=mock.ANY, id=uid)
        self.crud.execution.get_or_404.assert_awaited()

    def test_get_executions(self):
        """ Gets executions """
        self.crud.execution.page.return_value = {}

        job = uuid.uuid4()
        query = {'page': 7, 'size': 4}
        response = self.app\
            .get(f'/tasks/nice/jobs/{job}/executions', params=query)

        self.assertEqual(response.status_code, 200)

        self.crud.execution.page\
            .assert_called_once_with(job=mock.ANY, page=7, size=4)
        self.crud.execution.page.assert_awaited()