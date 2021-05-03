from fastapi import Depends
from pydantic import BaseModel

from . import router
from newlane.api import deps
from newlane.db import db
from newlane import docker
from newlane.queue import queue
from newlane.models import Task, Job, Execution


class PostNewTask(BaseModel):
    image: str
    command: str


@router.post('/{task}')
async def post_task(task: str, body: PostNewTask) -> Task:
    task = Task(name=task)
    job = Job(image=body.image, command=body.command, task=task)
    execution = Execution(job=job)
    await db.save(execution)

    execution = str(execution.id)
    queue.enqueue(docker.execute, execution, body.image, body.command)

    return task


@router.get('/{task}')
async def get_task(task: Task = Depends(deps.get_task)):
    jobs = await db.find(Job, Job.task == task.id)
    return {
        'taskId': task.name,
        'jobs': [{'id': str(j.id)} for j in jobs]
    }


@router.get('/')
async def get_tasks():
    tasks = await db.find(Task)
    return {'items': tasks}
