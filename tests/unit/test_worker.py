from unittest import mock
from unittest import IsolatedAsyncioTestCase

from newlane import worker


@mock.patch('newlane.worker.crud', autospec=True)
@mock.patch('newlane.worker.core', autospec=True)
class TestWorker(IsolatedAsyncioTestCase):
    async def test_cron(self, core, crud):
        """ Creates new execution and enqueues it """
        await worker.cron('nice')
        crud.job.get.assert_called_once_with(id='nice')
        crud.job.get.assert_awaited()
        crud.execution.create.assert_called_once_with(job=mock.ANY)
        crud.execution.create.assert_awaited()
        core.get_queue.assert_called_once_with()
        core.get_queue().enqueue.assert_called_once_with(mock.ANY, mock.ANY)
        crud.execution.save.assert_called_once_with(mock.ANY)
        crud.execution.save.assert_awaited()

    async def test_pull(self, core, crud):
        """ Pulls docker image and updates execution """
        await worker.pull('nice')
        crud.execution.get.assert_called_once_with(id='nice')
        crud.execution.get.assert_awaited()
        core.get_queue.assert_called_once_with()
        core.get_queue().enqueue.assert_called_once_with(mock.ANY, 'nice')
        calls = [mock.call(mock.ANY), mock.call(mock.ANY)]
        self.assertListEqual(crud.execution.save.call_args_list, calls)

    async def test_run(self, core, crud):
        """ Executes command inside docker image and updates execution """
        await worker.run('nice')
        crud.execution.get.assert_called_once_with(id='nice')
        crud.execution.get.assert_awaited()
        core.get_docker.assert_called_once_with()
        core.get_docker().containers.run.assert_called_once_with(
            image=mock.ANY,
            command=mock.ANY,
            environment=mock.ANY
        )

        calls = [mock.call(mock.ANY), mock.call(mock.ANY)]
        self.assertListEqual(crud.execution.save.call_args_list, calls)
