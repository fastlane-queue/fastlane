import uuid
from unittest import mock
from unittest import TestCase
from datetime import timedelta

from fastapi import HTTPException
from fastapi.testclient import TestClient

from newlane import app


class TestApiJobs(TestCase):
    def setUp(self):
        self.core = mock\
            .patch('newlane.api.jobs.core', autospec=True)\
            .start()
        self.crud = mock\
            .patch('newlane.api.jobs.crud', autospec=True)\
            .start()
        self.app = TestClient(app.app)

    def tearDown(self):
        mock.patch.stopall()

    def test_post_job(self):
        """ Posts job """
        self.crud.job.create.return_value = {}

        data = {'image': 'hello-world', 'command': './hello'}
        response = self.app.post('/tasks/nice/jobs/', json=data)

        self.assertEqual(response.status_code, 200)

        self.core.get_scheduler.assert_called_once_with()
        self.crud.task.get_or_404.assert_called_once_with(name='nice')
        self.crud.task.get_or_404.assert_awaited()
        self.crud.job.create.assert_called_once_with(
            task=mock.ANY,
            image='hello-world',
            command='./hello',
            environment={},
            cron=None
        )
        self.crud.job.create.assert_awaited()

    def test_post_job_start_in(self):
        """ Posts job with `start_in` """
        self.crud.job.create.return_value = {}

        data = {'image': 'hello-world', 'command': './hello', 'start_in': 123}
        response = self.app.post('/tasks/nice/jobs/', json=data)

        self.assertEqual(response.status_code, 200)

        self.crud.execution.create.assert_called_once_with(job=mock.ANY)
        self.crud.execution.create.assert_awaited()
        self.core.get_scheduler().enqueue_in.assert_called_once_with(
            timedelta(seconds=123),
            mock.ANY,
            mock.ANY
        )
        self.crud.execution.save.assert_called_once_with(mock.ANY)
        self.crud.execution.save.assert_awaited()

    def test_post_job_cron(self):
        """ Posts job with `cron` """
        # FastAPI has problems if it tries to desserialize a `mock.Mock` into
        # a JSON. That is why we use `mock.MagicMock` here instead of a simple
        # `mock.Mock`
        job = mock.MagicMock()
        job.id = 'nice'
        self.crud.job.create.return_value = job

        data = {
            'image': 'hello-world',
            'command': './hello',
            'cron': '* * * * *'
        }
        response = self.app.post('/tasks/nice/jobs/', json=data)

        self.assertEqual(response.status_code, 200)

        self.core.get_scheduler().cron.assert_called_once_with(
            '* * * * *',
            func=mock.ANY,
            args=['nice']
        )

    def test_get_job(self):
        """ Gets job """
        self.crud.job.get_or_404.return_value = {}

        uid = uuid.uuid4()
        response = self.app.get(f'/tasks/nice/jobs/{uid}')

        self.assertEqual(response.status_code, 200)

        self.crud.task.get_or_404.assert_called_once_with(name='nice')
        self.crud.task.get_or_404.assert_awaited()
        self.crud.job.get_or_404.assert_called_once_with(task=mock.ANY, id=uid)
        self.crud.job.get_or_404.assert_awaited()

    def test_get_job_404(self):
        """ Gets job, 404 """
        self.crud.job.get_or_404.side_effect = HTTPException(404)

        uid = uuid.uuid4()
        response = self.app.get(f'/tasks/nice/jobs/{uid}')

        self.assertEqual(response.status_code, 404)

        self.crud.task.get_or_404.assert_called_once_with(name='nice')
        self.crud.task.get_or_404.assert_awaited()
        self.crud.job.get_or_404.assert_called_once_with(task=mock.ANY, id=uid)
        self.crud.job.get_or_404.assert_awaited()

    def test_get_jobs(self):
        """ Get jobs """
        self.crud.job.page.return_value = {}

        params = {'page': 7, 'size': 4}
        response = self.app.get(f'/tasks/nice/jobs', params=params)

        self.assertEqual(response.status_code, 200)

        self.crud.task.get_or_404.assert_called_once_with(name='nice')
        self.crud.task.get_or_404.assert_awaited()
        self.crud.job.page\
            .assert_called_once_with(task=mock.ANY, page=7, size=4)
        self.crud.job.page.assert_awaited()
