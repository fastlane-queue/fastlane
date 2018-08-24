from unittest.mock import MagicMock
from uuid import uuid4

from preggy import expect
from rq import Queue, SimpleWorker

import easyq.worker.job as job_mod
from easyq.models.task import Task


def test_run_job(client):
    '''Test run job does not fail if no job available'''
    with client.application.app_context():
        task_id = str(uuid4())
        t = Task.create_task(task_id, 'container', 'command')
        exec_mock = MagicMock()
        client.application.executor = exec_mock()
        queue = Queue(
            'tasks', is_async=False, connection=client.application.redis)
        queue.enqueue(job_mod.add_task, t.task_id)

        worker = SimpleWorker([queue], connection=queue.connection)
        worker.work(burst=True)

        t.reload()
        expect(t.jobs).to_length(1)
        expect(t.jobs[0].image).to_equal(t.image)
        expect(t.jobs[0].command).to_equal(t.command)
