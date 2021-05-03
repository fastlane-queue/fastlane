import bson
import odmantic.query
from pydantic import BaseModel
from starlette.responses import PlainTextResponse
from fastapi import APIRouter, HTTPException, Depends

from newlane.api import deps
from newlane.db import db
from newlane import docker
from newlane.queue import queue
from newlane.models import Task, Job, Execution

router = APIRouter(prefix='/tasks')


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


@router.put('/{task}/jobs/{job}')
async def put_task_job(job: Job = Depends(deps.get_job)):
    return job


@router.get('/{task}/jobs/{job}')
async def get_task_job(job: Job = Depends(deps.get_job)):
    return {
        'image': job.image,
        'command': job.command,
        'envs': {},
        'metadata': job.metadata,
        'retries': 0
    }


@router.get('/{task}/jobs/{job}/logs')
async def get_task_job_logs(job: Job = Depends(deps.get_job)):
    execution = await db.find_one(
        Execution, 
        Execution.job == job.id, 
        sort=odmantic.query.desc(Execution.created_at)
    )
    return PlainTextResponse(execution.log)


@router.get('/{task}/jobs/{job}/stdout')
async def get_task_job_stdout(task: str, job: str):
    pass


@router.get('/{task}/jobs/{job}/stderr')
async def get_task_job_stderr(task: str, job: str):
    pass


@router.post('/{task}/jobs/{job}/stop')
async def post_task_job_stop(task: str, job: str):
    pass


@router.get('/{task}/jobs/{job}/stream')
async def get_task_job_stream(task: str, job: str):
    pass


@router.get('/{task}/jobs/{job}/executions/{exec}')
async def get_task_job_execution(task: str, job: str, exec: str):
    pass


@router.get('/{task}/jobs/{job}/executions/{exec}/logs')
async def get_task_job_execution_logs(task: str, job: str, exec: str):
    pass


@router.get('/{task}/jobs/{job}/executions/{exec}/stdout')
async def get_task_job_execution_stdout(task: str, job: str, exec: str):
    pass


@router.get('/{task}/jobs/{job}/executions/{exec}/stderr')
async def get_task_job_execution_stderr(task: str, job: str, exec: str):
    pass


@router.post('/{task}/jobs/{job}/executions/{exec}/stop')
async def post_task_job_execution_stop(task: str, job: str, exec: str):
    pass


@router.get('/{task}/jobs/{job}/stream/executions/{exec}')
async def get_task_job_execution_stream(task: str, job: str, exec: str):
    pass