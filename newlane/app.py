from fastapi import FastAPI
from pydantic import BaseModel
from redis.utils import pipeline
from starlette import status
from starlette.responses import JSONResponse

from .db import db
from .queue import queue
from .docker import execute
from .models import Task, Job, Execution

app = FastAPI()

class PostNewTask(BaseModel):
    image: str
    command: str


@app.post('/tasks/{task}')
async def post_task(task: str, body: PostNewTask) -> Task:
    task = Task(name=task)
    job = Job(image=body.image, command=body.command, task=task)
    execution = Execution(job=job)
    await db.save(execution)

    id = str(execution.id)
    queue.enqueue(execute, id, body.image, body.command)

    return task
