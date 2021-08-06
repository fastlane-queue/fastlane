import uuid
from unittest import mock
from datetime import timedelta
from unittest import IsolatedAsyncioTestCase

from fastapi import HTTPException

from newlane.api import jobs
from newlane.api import payloads


@mock.patch('newlane.api.jobs.core', autospec=True)
@mock.patch('newlane.api.jobs.crud', autospec=True)
class TestApiJobs(IsolatedAsyncioTestCase):

    # Mock starlette.requests.Request object
    class request:
        class client:
            host = '127.0.0.1'

    async def test_post_job(self, crud, core):
        """ Posts job """
        crud.job.create.return_value = {}
        crud.task.get_or_404.return_value = {}

        data = payloads.Job(image='hello-world', command='./hello')
        response = await jobs.post_job('nice', data, self.request)

        self.assertDictEqual(response, {})

        core.get_scheduler.assert_called_once_with()
        crud.task.get_or_404.assert_called_once_with(name='nice')
        crud.task.get_or_404.assert_awaited()
        crud.job.create.assert_called_once_with(
            task=mock.ANY,
            image='hello-world',
            command='./hello',
            environment={},
            cron=None,
            created_by=self.request.client.host
        )
        crud.job.create.assert_awaited()

    async def test_post_job_start_in(self, crud, core):
        """ Posts job with `start_in` """
        crud.job.create.return_value = {}

        data = payloads\
            .Job(image='hello-world', command='./hello', start_in=123)
        response = await jobs.post_job('nice', data, self.request)

        self.assertDictEqual(response, {})

        crud.execution.create.assert_called_once_with(job=mock.ANY)
        crud.execution.create.assert_awaited()
        core.get_scheduler().enqueue_in.assert_called_once_with(
            timedelta(seconds=123),
            mock.ANY,
            mock.ANY
        )
        crud.execution.save.assert_called_once_with(mock.ANY)
        crud.execution.save.assert_awaited()

    async def test_post_job_cron(self, crud, core):
        """ Posts job with `cron` """
        value = mock.Mock()
        value.id = 'nice'
        crud.job.create.return_value = value

        data = payloads\
            .Job(image='hello-world', command='./hello', cron='* * * * *')
        response = await jobs.post_job('nice', data, self.request)

        self.assertIs(response, value)

        core.get_scheduler().cron.assert_called_once_with(
            '* * * * *',
            func=mock.ANY,
            args=['nice']
        )

    async def test_get_job(self, crud, core):
        """ Gets job """
        crud.job.get_or_404.return_value = {}

        uid = uuid.uuid4()
        response = await jobs.get_job('nice', uid)

        self.assertDictEqual(response, {})

        crud.task.get_or_404.assert_called_once_with(name='nice')
        crud.task.get_or_404.assert_awaited()
        crud.job.get_or_404.assert_called_once_with(task=mock.ANY, id=uid)
        crud.job.get_or_404.assert_awaited()

    async def test_get_job_404(self, crud, core):
        """ Gets job, 404 """
        crud.job.get_or_404.side_effect = HTTPException(404)

        uid = uuid.uuid4()

        with self.assertRaises(HTTPException):
            await jobs.get_job('nice', uid)

        crud.task.get_or_404.assert_called_once_with(name='nice')
        crud.task.get_or_404.assert_awaited()
        crud.job.get_or_404.assert_called_once_with(task=mock.ANY, id=uid)
        crud.job.get_or_404.assert_awaited()

    async def test_get_jobs(self, crud, core):
        """ Get jobs """
        crud.job.page.return_value = {}

        response = await jobs.get_jobs('nice', page=7, size=4)

        self.assertDictEqual(response, {})

        crud.task.get_or_404.assert_called_once_with(name='nice')
        crud.task.get_or_404.assert_awaited()
        crud.job.page.assert_called_once_with(task=mock.ANY, page=7, size=4)
        crud.job.page.assert_awaited()
