from datetime import datetime, timedelta
from uuid import uuid4

from preggy import expect
from rq import Queue
from rq_scheduler import Scheduler

import easyq.worker.job as job_mod
from easyq.worker.scheduler import QueueScheduler


def test_schedule_jobs(client):
    '''Test moving jobs to proper queue'''
    with client.application.app_context():
        app = client.application
        app.redis.flushall()

        task_id = str(uuid4())
        job_id = str(uuid4())

        past = datetime.now() - timedelta(days=10)

        queue = Queue('run_job', is_async=False, connection=app.redis)
        scheduler = Scheduler(queue, connection=app.redis)

        scheduler.enqueue_at(
            past, job_mod.run_job, task_id, job_id, timeout=-1)
        scheduled_jobs_key = 'rq:scheduler:scheduled_jobs'

        res = app.redis.exists(scheduled_jobs_key)
        expect(res).to_be_true()

        res = app.redis.zcard(scheduled_jobs_key)
        expect(res).to_equal(1)

        job_ids = app.redis.zrangebyscore(
            scheduled_jobs_key, min=0, max="+inf")
        expect(job_ids).to_length(1)

        curr_job_id = job_ids[0].decode('utf-8')
        expect(curr_job_id).not_to_be_null()

        hash_key = f'rq:job:{curr_job_id}'
        res = app.redis.exists(hash_key)
        expect(res).to_be_true()

        res = app.redis.hget(hash_key, 'status')
        expect(res).to_be_null()

        res = app.redis.hexists(hash_key, 'data')
        expect(res).to_be_true()

        res = app.redis.hget(hash_key, 'description')
        expect(res).to_equal(
            f"easyq.worker.job.run_job('{task_id}', '{job_id}')")

        res = app.redis.hget(hash_key, 'timeout')
        expect(res).to_equal('-1')

        res = app.redis.hget(hash_key, 'origin')
        expect(res).to_equal('<Queue run_job>')


def test_move_scheduled_jobs(client):
    '''Test moving jobs to proper queue'''
    with client.application.app_context():
        app = client.application
        app.redis.flushall()

        task_id = str(uuid4())
        job_id = str(uuid4())

        past = datetime.now() - timedelta(days=10)
        future = datetime.now() + timedelta(days=10)

        scheduler = Scheduler(queue_name='jobs', connection=app.redis)

        scheduler.enqueue_at(
            past, job_mod.run_job, task_id, job_id, timeout=-1)

        scheduler.enqueue_at(
            future, job_mod.run_job, task_id, job_id, timeout=-1)

        q = 'rq:queue:jobs'
        res = app.redis.llen(q)
        expect(res).to_equal(0)

        qs = QueueScheduler('jobs', app)
        qs.move_jobs()

        q = 'rq:queue:jobs'
        res = app.redis.llen(q)
        expect(res).to_equal(1)

        scheduler.enqueue_at(
            past, job_mod.run_job, task_id, job_id, timeout=-1)

        qs = QueueScheduler('jobs', app)
        qs.move_jobs()

        res = app.redis.llen(q)
        expect(res).to_equal(2)
