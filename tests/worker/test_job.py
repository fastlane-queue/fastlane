from datetime import datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

from preggy import expect
from rq import Queue, SimpleWorker

import fastlane.worker.job as job_mod
from fastlane.models.job import JobExecution
from fastlane.models.task import Task


def test_run_job(client):
    """Test running a new job for a task"""
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

        queue = Queue("jobs", is_async=False, connection=client.application.redis)
        result = queue.enqueue(job_mod.run_job, t.task_id, job_id, "image", "command")

        worker = SimpleWorker([queue], connection=queue.connection)
        worker.work(burst=True)

        t.reload()
        expect(t.jobs).to_length(1)

        job = t.jobs[0]
        expect(job.executions).to_length(1)

        execution = job.executions[0]
        expect(execution.image).to_equal("image")
        expect(execution.command).to_equal("command")

        hash_key = f"rq:job:{result.id}"

        res = app.redis.exists(hash_key)
        expect(res).to_be_true()

        res = app.redis.hget(hash_key, "status")
        expect(res).to_equal("finished")

        res = app.redis.hexists(hash_key, "data")
        expect(res).to_be_true()

        keys = app.redis.keys()
        next_job_id = [
            key

            for key in keys

            if key.decode("utf-8").startswith("rq:job")
            and not key.decode("utf-8").endswith(result.id)
        ]
        expect(next_job_id).to_length(1)
        next_job_id = next_job_id[0]

        res = app.redis.exists(next_job_id)
        expect(res).to_be_true()

        res = app.redis.hget(next_job_id, "status")
        expect(res).to_equal("queued")

        res = app.redis.hexists(next_job_id, "data")
        expect(res).to_be_true()

        res = app.redis.hget(next_job_id, "origin")
        expect(res).to_equal("monitor")

        res = app.redis.hget(next_job_id, "description")
        expect(res).to_equal(
            f"fastlane.worker.job.monitor_job('{task_id}', '{job_id}', '{execution.execution_id}')"
        )

        res = app.redis.hget(next_job_id, "timeout")
        expect(res).to_equal("-1")

        t.reload()
        expect(t.jobs[0].executions[0].status).to_equal(JobExecution.Status.running)


def test_monitor_job_with_retry(client):
    """Test monitoring a job for a task that fails"""
    with client.application.app_context():
        app = client.application
        app.redis.flushall()

        task_id = str(uuid4())
        t = Task.create_task(task_id)
        j = t.create_job()
        job_id = j.job_id
        j.metadata["retries"] = 3
        j.metadata["retry_count"] = 0

        ex = j.create_execution("image", "command")

        j.save()

        exec_mock = MagicMock()
        exec_mock.get_result.return_value = MagicMock(
            exit_code=1, log="".encode("utf-8"), error="error".encode("utf-8")
        )

        exec_class_mock = MagicMock()
        exec_class_mock.Executor.return_value = exec_mock
        client.application.executor_module = exec_class_mock

        queue = Queue("monitor", is_async=False, connection=client.application.redis)
        result = queue.enqueue(job_mod.monitor_job, t.task_id, job_id, ex.execution_id)

        worker = SimpleWorker([queue], connection=queue.connection)
        worker.work(burst=True)

        t.reload()
        expect(t.jobs).to_length(1)

        job = t.jobs[0]
        expect(job.executions).to_length(1)

        execution = job.executions[0]
        expect(execution.image).to_equal("image")
        expect(execution.command).to_equal("command")

        hash_key = f"rq:job:{result.id}"

        res = app.redis.exists(hash_key)
        expect(res).to_be_true()

        res = app.redis.hget(hash_key, "status")
        expect(res).to_equal("finished")

        res = app.redis.hexists(hash_key, "data")
        expect(res).to_be_true()

        res = app.redis.zrange(b"rq:scheduler:scheduled_jobs", 0, -1)
        expect(res).to_length(1)

        time = datetime.now() + timedelta(seconds=2)
        res = app.redis.zscore("rq:scheduler:scheduled_jobs", res[0])
        expect(int(res)).to_equal(int(time.timestamp()))

        nj = app.redis.zrange("rq:scheduler:scheduled_jobs", 0, 0)[0].decode("utf-8")
        next_job_id = f"rq:job:{nj}"
        res = app.redis.exists(next_job_id)
        expect(res).to_be_true()

        res = app.redis.hexists(next_job_id, "data")
        expect(res).to_be_true()

        res = app.redis.hget(next_job_id, "origin")
        expect(res).to_equal("jobs")

        res = app.redis.hget(next_job_id, "description")
        expect(res).to_equal(
            f"fastlane.worker.job.run_job('{task_id}', '{job_id}', 'image', 'command')"
        )

        t.reload()
        expect(t.jobs[0].executions[0].status).to_equal(JobExecution.Status.done)


def test_monitor_job_with_retry2(client):
    """Test monitoring a job for a task that fails stops after max retries"""
    with client.application.app_context():
        app = client.application
        app.redis.flushall()

        task_id = str(uuid4())
        t = Task.create_task(task_id)
        j = t.create_job()
        job_id = j.job_id
        j.metadata["retries"] = 3
        j.metadata["retry_count"] = 3

        ex = j.create_execution("image", "command")

        j.save()

        exec_mock = MagicMock()
        exec_mock.get_result.return_value = MagicMock(
            exit_code=1, log="".encode("utf-8"), error="error".encode("utf-8")
        )

        exec_class_mock = MagicMock()
        exec_class_mock.Executor.return_value = exec_mock
        client.application.executor_module = exec_class_mock

        queue = Queue("monitor", is_async=False, connection=client.application.redis)
        result = queue.enqueue(job_mod.monitor_job, t.task_id, job_id, ex.execution_id)

        worker = SimpleWorker([queue], connection=queue.connection)
        worker.work(burst=True)

        t.reload()
        expect(t.jobs).to_length(1)

        job = t.jobs[0]
        expect(job.executions).to_length(1)

        execution = job.executions[0]
        expect(execution.image).to_equal("image")
        expect(execution.command).to_equal("command")

        hash_key = f"rq:job:{result.id}"

        res = app.redis.exists(hash_key)
        expect(res).to_be_true()

        res = app.redis.hget(hash_key, "status")
        expect(res).to_equal("finished")

        res = app.redis.hexists(hash_key, "data")
        expect(res).to_be_true()

        keys = app.redis.keys()
        next_job_id = [
            key

            for key in keys

            if key.decode("utf-8").startswith("rq:job")
            and not key.decode("utf-8").endswith(result.id)
        ]
        expect(next_job_id).to_length(0)
