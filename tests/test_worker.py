from unittest import mock
from unittest import IsolatedAsyncioTestCase

from newlane import worker

class TestWorker(IsolatedAsyncioTestCase):
    def setUp(self):
        worker.core = mock.Mock()

        worker.crud = mock.Mock()
        worker.crud.job = mock.AsyncMock()
        worker.crud.execution = mock.AsyncMock()

    async def test_cron(self):
        """ Creates new execution and enqueues it """
        await worker.cron('nice')
        worker.crud.job.get.assert_called_once_with(id='nice')
        worker.crud.job.get.assert_awaited()
        worker.crud.execution.create.assert_called_once_with(job=mock.ANY)
        worker.crud.execution.create.assert_awaited()
        worker.core.get_queue.assert_called_once_with()
        worker.core.get_queue().enqueue\
            .assert_called_once_with(mock.ANY, mock.ANY)
        worker.crud.execution.save.assert_called_once_with(mock.ANY)
        worker.crud.execution.save.assert_awaited()

    async def test_pull(self):
        """ Pulls docker image and updates execution """
        await worker.pull('nice')
        worker.crud.execution.get.assert_called_once_with(id='nice')
        worker.crud.execution.get.assert_awaited()
        worker.core.get_queue.assert_called_once_with()
        worker.core.get_queue().enqueue\
            .assert_called_once_with(mock.ANY, 'nice')

        calls = [mock.call(mock.ANY), mock.call(mock.ANY)]
        self.assertListEqual(worker.crud.execution.save.call_args_list, calls)

    async def test_run(self):
        """ Executes command inside docker image and updates execution """
        await worker.run('nice')
        worker.crud.execution.get.assert_called_once_with(id='nice')
        worker.crud.execution.get.assert_awaited()
        worker.core.get_docker.assert_called_once_with()
        worker.core.get_docker().containers.run.assert_called_once_with(
            image=mock.ANY,
            command=mock.ANY,
            environment=mock.ANY
        )

        calls = [mock.call(mock.ANY), mock.call(mock.ANY)]
        self.assertListEqual(worker.crud.execution.save.call_args_list, calls)
