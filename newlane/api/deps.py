from uuid import UUID

from fastapi import HTTPException, Depends

from newlane import crud
from newlane.models import Task, Job, Execution


async def get_task(task: str) -> Task:
    model = await crud.task.get(name=task)

    if model is None:
        detail = f"Task '{task}' not found"
        raise HTTPException(status_code=404, detail=detail)

    return model


async def get_job(job: UUID, task: Task = Depends(get_task)) -> Job:
    model = await crud.job.get(task=task.id, id=job)

    if model is None:
        detail = f"Job '{job}' not found"
        raise HTTPException(status_code=404, detail=detail)

    return model


async def get_execution(execution: UUID, job: Job = Depends(get_job)) -> Execution:  # noqa
    model = await crud.execution.get(job=job.id, id=execution)

    if model is None:
        detail = f"Execution '{execution}' not found"
        raise HTTPException(status_code=404, detail=detail)

    return model
