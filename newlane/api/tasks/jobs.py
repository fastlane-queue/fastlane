import bson
from fastapi import APIRouter, Depends
from starlette.responses import PlainTextResponse

from . import router
from newlane.api import deps, payloads
from newlane.core import db
from newlane.models import Task, Job, Execution


@router.put('/{task}/jobs/{job}')
async def put_task_job(task: str, job: str, body: payloads.Job) -> dict:
    task = await deps.get_task(task)

    job = bson.ObjectId(job)
    job = await db.find_one(Job, Job.task == task.id, Job.id == job)
    if job is None:
        job = body.dict()
        job = Job(**body)
    else:
        job.image = body.image
        job.command = body.command
        job.metadata = body.metadata


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
    execution = await db.find_one(
        Execution,
        Execution.job == job.id,
        sort=odmantic.query.desc(Execution.created_at)
    )
    return PlainTextResponse(execution.log)


@router.get('/{task}/jobs/{job}/stderr')
async def get_task_job_stderr(task: str, job: str):
    execution = await db.find_one(
        Execution,
        Execution.job == job.id,
        sort=odmantic.query.desc(Execution.created_at)
    )
    return PlainTextResponse(execution.error)


@router.post('/{task}/jobs/{job}/stop')
async def post_task_job_stop(task: str, job: str):
    raise NotImplementedError()


@router.get('/{task}/jobs/{job}/stream')
async def get_task_job_stream(task: str, job: str):
    raise NotImplementedError()
