from json import loads

from preggy import expect

from easyq.models.task import Task


def test_enqueue1(client):
    """Test enqueue a job works"""

    data = {
        "container": "ubuntu",
        "command": "ls",
    }

    rv = client.post('/tasks', data=data, follow_redirects=True)

    obj = loads(rv.data)
    expect(obj['jobId']).not_to_be_null()
    expect(obj['status']).to_equal("queued")

    hash_key = f'rq:job:{obj["jobId"]}'
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
    expect(res).to_equal('tasks')

    res = app.redis.hget(hash_key, 'description')
    expect(res).to_equal(f"easyq.worker.job.add_task('{obj['taskId']}')")

    res = app.redis.hget(hash_key, 'timeout')
    expect(res).to_equal('-1')

    task = Task.get_by_task_id(obj['taskId'])
    expect(task).not_to_be_null()
    expect(task.jobs).to_be_empty()
    expect(task.done).to_be_false()
