from fastapi import Depends
from pydantic import BaseModel

from . import router
from newlane import worker
from newlane.api import deps
from newlane.models import Task, Job, Execution
from newlane.settings.db import db
from newlane.settings.queue import queue


class PostNewTask(BaseModel):
    image: str
    command: str


@router.post('/{name}')
async def post_task(name: str, body: PostNewTask) -> dict:
    task = await db.find_one(Task, Task.name == name)
    if task is None:
        task = Task(name=name)

    job = Job(image=body.image, command=body.command, task=task)
    execution = Execution(job=job)
    await db.save(execution)

    execution = str(execution.id)
    queue.enqueue(worker.run_container, execution, body.image, body.command)

    return task


@router.get('/{task}')
async def get_task(task: Task = Depends(deps.get_task)) -> dict:
    jobs = await db.find(Job, Job.task == task.id)
    return {
        'taskId': task.name,
        'jobs': [{'id': str(j.id)} for j in jobs]
    }


@router.get('/')
async def get_tasks() -> dict:
    tasks = await db.find(Task)
    return {'items': tasks}
