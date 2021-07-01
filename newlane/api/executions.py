from uuid import UUID
from fastapi import APIRouter

from newlane import core
from newlane import crud
from newlane import worker

router = APIRouter(prefix='/tasks/{task}/jobs/{job}/executions')


@router.post('/')
async def post_execution(task: str, job: UUID):
    task = await crud.task.get_or_404(name=task)
    job = await crud.job.get_or_404(task=task.id, id=job)
    execution = await crud.execution.create(job=job)

    queue = core.get_queue()
    message = queue.enqueue(worker.pull, execution.id)
    execution.message.id = message.id

    return await crud.execution.save(execution)


@router.get('/{execution}/')
async def get_execution(task: str, job: UUID, execution: UUID):
    task = await crud.task.get_or_404(name=task)
    job = await crud.job.get_or_404(task=task.id, id=job)
    return await crud.execution.get_or_404(job=job.id, id=execution)


@router.get('/')
async def get_executions(task: str, job: UUID, page: int = 1, size: int = 10):
    task = await crud.task.get_or_404(name=task)
    job = await crud.job.get_or_404(task=task.id, id=job)
    return await crud.execution.page(job=job.id, page=page, size=size)
