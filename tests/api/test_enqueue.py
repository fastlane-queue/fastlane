from json import loads
from uuid import uuid4

from preggy import expect

from easyq.models import db
from easyq.models.task import Task


def test_enqueue1(client):
    """Test enqueue a job works"""
    task_id = str(uuid4())

    data = {
        "image": "ubuntu",
        "command": "ls",
    }

    rv = client.post(f'/tasks/{task_id}', data=data, follow_redirects=True)

    obj = loads(rv.data)
    job_id = obj['jobId']
    expect(job_id).not_to_be_null()
    expect(obj['queueJobId']).not_to_be_null()
    expect(obj['status']).to_equal("queued")

    queue_job_id = obj["queueJobId"]
    hash_key = f'rq:job:{queue_job_id}'
    app = client.application

    res = app.redis.exists(hash_key)
    expect(res).to_be_true()

    res = app.redis.hget(hash_key, 'status')
    expect(res).to_equal('queued')

    res = app.redis.hexists(hash_key, 'created_at')
    expect(res).to_be_true()

    res = app.redis.hexists(hash_key, 'enqueued_at')
    expect(res).to_be_true()

    res = app.redis.hexists(hash_key, 'data')
    expect(res).to_be_true()

    res = app.redis.hget(hash_key, 'origin')
    expect(res).to_equal('jobs')

    res = app.redis.hget(hash_key, 'description')
    expect(res).to_equal(
        f"easyq.worker.job.run_job('{obj['taskId']}', '{job_id}')")

    res = app.redis.hget(hash_key, 'timeout')
    expect(res).to_equal('-1')

    task = Task.get_by_task_id(obj['taskId'])
    expect(task).not_to_be_null()
    expect(task.jobs).not_to_be_empty()

    j = task.jobs[0]
    expect(str(j.id)).to_equal(job_id)

    q = 'rq:queue:jobs'
    res = app.redis.llen(q)
    expect(res).to_equal(1)

    res = app.redis.lpop(q)
    expect(res).to_equal(queue_job_id)

    with client.application.app_context():
        count = Task.objects.count()
        expect(count).to_equal(1)


def test_enqueue2(client):
    """Test enqueue a job with the same task does not create a new task"""

    task_id = str(uuid4())

    data = {
        "image": "ubuntu",
        "command": "ls",
    }

    rv = client.post(f'/tasks/{task_id}', data=data, follow_redirects=True)
    obj = loads(rv.data)
    job_id = obj['jobId']
    expect(job_id).not_to_be_null()
    expect(obj['queueJobId']).not_to_be_null()
    expect(obj['status']).to_equal("queued")

    rv = client.post(f'/tasks/{task_id}', data=data, follow_redirects=True)
    obj = loads(rv.data)
    job_id = obj['jobId']
    expect(job_id).not_to_be_null()
    expect(obj['queueJobId']).not_to_be_null()
    expect(obj['status']).to_equal("queued")

    task = Task.get_by_task_id(obj['taskId'])
    expect(task).not_to_be_null()
    expect(task.jobs).not_to_be_empty()

    with client.application.app_context():
        count = Task.objects.count()
        expect(count).to_equal(1)
