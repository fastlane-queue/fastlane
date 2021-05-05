from uuid import UUID

import bson
from fastapi import APIRouter, Depends
from starlette.responses import PlainTextResponse

from . import router
from newlane import crud, services
from newlane.api import deps, payloads
from newlane.core import db
from newlane.models import Task, Job, Execution


@router.post('/{task}/jobs')
async def post_job(task: str, job: payloads.Job):
    task = await crud.task.get_or_404(name=task)
    return await crud.job.create(task=task, **job.dict())


@router.get('/{task}/jobs/{job}')
async def get_job(task: str, job: UUID):
    task = await crud.task.get_or_404(name=task)
    return await crud.job.get_or_404(task=task.id, id=job)


@router.get('/{task}/jobs')
async def get_jobs(task: str, page: int = 1, size: int = 10):
    task = await crud.task.get_or_404(name=task)
    return await crud.job.page(task=task.id, page=page, size=size)
