import bson
from fastapi import HTTPException

from newlane.db import db
from newlane.models import Task, Job, Execution


async def get_task(task: str) -> Task:
    task = await db.find_one(Task, Task.name == task)

    if task is None:
        detail = f"Task '{task}' not found"
        raise HTTPException(status_code=404, detail=detail)

    return task


async def get_job(task: str, job: str) -> Job:
    task = await get_task(task)

    job = bson.ObjectId(job)
    job = await db.find_one(Job, Job.task == task.id, Job.id == job)

    if job is None:
        detail = f"Job '{job}' not found"
        raise HTTPException(status_code=404, detail=detail)

    return job


async def get_execution(task: str, job: str, execution: str) -> Execution:
    job = await get_job(task, job)

    execution = bson.ObjectId(execution)
    execution = await db.find_one(
        Execution, 
        Execution.task == task.id, 
        Execution.id == execution
    )

    if execution is None:
        detail = f"Execution '{execution}' not found"
        raise HTTPException(status_code=404, detail=detail)

    return execution