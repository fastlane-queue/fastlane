from . import worker
from newlane import crud
from newlane.core.queue import queue
from newlane.models import Job


async def enqueue(job: Job):
    execution = await crud.execution.create(job=job)
    message = queue.enqueue(worker.run_container, execution.id)
    execution.message_id = message.id
    return await crud.execution.save(execution)
