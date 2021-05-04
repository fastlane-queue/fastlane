import math

from fastapi import Depends
from pydantic import BaseModel

from . import router
from newlane import crud, services
from newlane.api import deps, payloads
from newlane.models import Task, Job, Execution


@router.post('/{name}')
async def post_task(name: str, body: payloads.Job) -> dict:
    task = await crud.task.get(name=name)
    if task is None:
        task = await crud.task.create(name=name)

    job = await crud.job.create(
        image=body.image,
        command=body.command,
        task=task
    )

    execution = await crud.execution.create(job=job)

    message = services.queue.enqueue_exec(
        execution.id,
        body.image,
        body.command
    )

    return {
        'executionId': str(execution.id),
        'executionUrl': 'TODO',
        'jobId': str(job.id),
        'jobUrl': 'TODO',
        'queueJobId': message.id,
        'taskId': str(task.name),
        'taskUrl': 'TODO'
    }


@router.get('/{task}')
async def get_task(task: Task = Depends(deps.get_task)) -> dict:
    jobs = await crud.job.find(task=task.id)
    jobs = [{'id': str(j.id), 'url': 'TODO'} for j in jobs]

    return {
        'taskId': task.name,
        'jobs': jobs
    }


@router.get('/')
async def get_tasks(page: int = 1, size: int = 10) -> dict:
    total = await crud.task.count()
    tasks = await crud.task.page(page=page, size=size)

    return {
        'hasNext': page * size < total,
        'hasPrev': (page - 1) * size > 0,
        'items': tasks,
        'nextUrl': 'TODO',
        'page': page,
        'pages': math.ceil(total / size),
        'perPage': size,
        'prevUrl': 'TODO',
        'total': total
    }
