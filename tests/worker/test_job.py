from unittest.mock import MagicMock
from uuid import uuid4

from preggy import expect
from rq import Queue, SimpleWorker

import easyq.worker.job as job_mod
from easyq.models.task import Task


def test_add_task(client):
    '''Test adding a new task'''
    with client.application.app_context():
        app = client.application
        app.redis.flushall()

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

        hash_key = f'rq:job:{t.jobs[0].job_id}'

        res = app.redis.exists(hash_key)
        expect(res).to_be_true()

        res = app.redis.hget(hash_key, 'status')
        expect(res).to_equal('finished')

        res = app.redis.hexists(hash_key, 'data')
        expect(res).to_be_true()

        job_id = t.jobs[0].job_id
        keys = app.redis.keys()
        next_job_id = [
            key for key in keys if key.decode('utf-8').startswith('rq:job')
            and not key.decode('utf-8').endswith(job_id)
        ]
        expect(next_job_id).to_length(1)
        next_job_id = next_job_id[0]

        res = app.redis.exists(next_job_id)
        expect(res).to_be_true()

        res = app.redis.hget(next_job_id, 'status')
        expect(res).to_equal('queued')

        res = app.redis.hexists(next_job_id, 'data')
        expect(res).to_be_true()

        res = app.redis.hget(next_job_id, 'origin')
        expect(res).to_equal('jobs')

        res = app.redis.hget(next_job_id, 'description')
        expect(res).to_equal(
            f"easyq.worker.job.run_job('{task_id}', '{job_id}')")

        res = app.redis.hget(next_job_id, 'timeout')
        expect(res).to_equal('-1')
