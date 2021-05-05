from uuid import UUID

from . import router
from newlane import crud


@router.post('/{task}/jobs/{job}/executions')
async def post_execution(task: str, job: UUID):
    task = await crud.task.get_or_404(name=task)
    job = await crud.job.get_or_404(task=task.id, id=job)
    return await crud.execution.create(job=job)


@router.get('/{task}/jobs/{job}/executions/{execution}')
async def get_execution(task: str, job: UUID, execution: UUID):
    task = await crud.task.get_or_404(name=task)
    job = await crud.job.get_or_404(task=task.id, id=job)
    return await crud.execution.get_or_404(job=job.id, id=execution)


@router.get('/{task}/jobs/{job}/executions')
async def get_executions(task: str, job: UUID, page: int = 1, size: int = 10):
    task = await crud.task.get_or_404(name=task)
    job = await crud.job.get_or_404(task=task.id, id=job)
    return await crud.execution.page(job=job.id, page=page, size=size)
