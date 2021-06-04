import uuid
from unittest import mock
from unittest import IsolatedAsyncioTestCase

from fastapi import HTTPException

from newlane.api import executions


@mock.patch('newlane.api.executions.core', autospec=True)
@mock.patch('newlane.api.executions.crud', autospec=True)
class TestApiExecutions(IsolatedAsyncioTestCase):
    async def test_post_execution(self, crud, core):
        """ Posts execution """
        crud.execution.save.return_value = {}

        job = uuid.uuid4()
        await executions.post_execution('nice', job)

        crud.task.get_or_404.assert_called_once_with(name='nice')
        crud.task.get_or_404.assert_awaited()
        crud.job.get_or_404.assert_called_once_with(task=mock.ANY, id=job)
        crud.job.get_or_404.assert_awaited()
        core.get_queue.assert_called_once_with()
        core.get_queue().enqueue.assert_called_once_with(mock.ANY, mock.ANY)
        crud.execution.save.assert_called_once_with(mock.ANY)
        crud.execution.save.assert_awaited()

    async def test_get_execution(self, crud, core):
        """ Gets execution """
        crud.execution.get_or_404.return_value = {}

        job = uuid.uuid4()
        uid = uuid.uuid4()
        await executions.get_execution('nice', job, uid)

        crud.execution.get_or_404.assert_called_once_with(job=mock.ANY, id=uid)
        crud.execution.get_or_404.assert_awaited()

    async def test_get_execution_404(self, crud, core):
        """ Gets execution, 404 """
        crud.execution.get_or_404.side_effect = HTTPException(404)

        job = uuid.uuid4()
        uid = uuid.uuid4()

        with self.assertRaises(HTTPException):
            await executions.get_execution('nice', job, uid)

        crud.execution.get_or_404.assert_called_once_with(job=mock.ANY, id=uid)
        crud.execution.get_or_404.assert_awaited()

    async def test_get_executions(self, crud, core):
        """ Gets executions """
        crud.execution.page.return_value = {}

        job = uuid.uuid4()
        query = {'page': 7, 'size': 4}

        await executions.get_executions('nice', job, page=7, size=4)

        crud.execution.page\
            .assert_called_once_with(job=mock.ANY, page=7, size=4)
        crud.execution.page.assert_awaited()
