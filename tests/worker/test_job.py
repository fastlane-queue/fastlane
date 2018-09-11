from unittest.mock import MagicMock
from uuid import uuid4

from preggy import expect
from rq import Queue, SimpleWorker

import easyq.worker.job as job_mod
from easyq.models.job import Job
from easyq.models.task import Task


def test_run_job(client):
    '''Test running a new job for a task'''
    with client.application.app_context():
        app = client.application
        app.redis.flushall()

        task_id = str(uuid4())
        t = Task.create_task(task_id)
        j = t.create_job()
        job_id = j.job_id
        t.save()

        exec_mock = MagicMock()

        exec_class_mock = MagicMock()
        exec_class_mock.Executor.return_value = exec_mock
        client.application.executor_module = exec_class_mock

        queue = Queue(
            'jobs', is_async=False, connection=client.application.redis)
        result = queue.enqueue(job_mod.run_job, t.task_id, job_id, 'image',
                               'command')

        worker = SimpleWorker([queue], connection=queue.connection)
        worker.work(burst=True)

        t.reload()
        expect(t.jobs).to_length(1)

        job = t.jobs[0]
        expect(job.executions).to_length(1)

        execution = job.executions[0]
        expect(execution.image).to_equal('image')
        expect(execution.command).to_equal('command')

        hash_key = f'rq:job:{result.id}'

        res = app.redis.exists(hash_key)
        expect(res).to_be_true()

        res = app.redis.hget(hash_key, 'status')
        expect(res).to_equal('finished')

        res = app.redis.hexists(hash_key, 'data')
        expect(res).to_be_true()

        keys = app.redis.keys()
        next_job_id = [
            key for key in keys if key.decode('utf-8').startswith('rq:job')
            and not key.decode('utf-8').endswith(result.id)
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
        expect(res).to_equal('monitor')

        res = app.redis.hget(next_job_id, 'description')
        expect(res).to_equal(
            f"easyq.worker.job.monitor_job('{task_id}', '{job_id}', '{execution.execution_id}')"
        )

        res = app.redis.hget(next_job_id, 'timeout')
        expect(res).to_equal('-1')

        t.reload()
        expect(t.jobs[0].executions[0].status).to_equal(Job.Status.running)
