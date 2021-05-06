from uuid import UUID

from . import router
from newlane import crud
from newlane.api import payloads
from newlane.services import worker
from newlane.core.queue import queue, scheduler


@router.post('/{task}/jobs')
async def post_job(task: str, body: payloads.Job):
    task = await crud.task.get_or_404(name=task)
    job = await crud.job.create(
        task=task, 
        image=body.image,
        command=body.command,
        environment=body.environment,
        cron=body.cron
    )

    if body.start_in:
        execution = await crud.execution.create(job=job)
        message = queue.enqueue_in(body.start_in, worker.pull, execution.id)
        execution.message.id = message.id
        await crud.execution.save(execution)
    
    if job.cron:
        scheduler.cron(job.cron, func=worker.cron, args=[job.id])
    
    return job



@router.get('/{task}/jobs/{job}')
async def get_job(task: str, job: UUID):
    task = await crud.task.get_or_404(name=task)
    return await crud.job.get_or_404(task=task.id, id=job)


@router.get('/{task}/jobs')
async def get_jobs(task: str, page: int = 1, size: int = 10):
    task = await crud.task.get_or_404(name=task)
    return await crud.job.page(task=task.id, page=page, size=size)
