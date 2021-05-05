from uuid import UUID
from datetime import datetime

from newlane import crud
from newlane.models import Execution, Status
from newlane.core.docker import docker
from newlane.core.queue import queue, scheduler


async def pull(id: UUID):
    execution = await crud.execution.get(id=id)

    # Update status
    execution.updated_at = datetime.utcnow()
    execution.status = Status.pulling
    await crud.execution.save(execution)

    # Pull
    docker.images.pull(execution.job.image)

    # Next
    message = queue.enqueue(run, id)
    execution.message.id = message.id

    return await crud.execution.save(execution)


async def run(id: UUID):
    execution = await crud.execution.get(id=id)

    # Update
    execution.started_at = datetime.utcnow()
    execution.status = Status.running
    execution.updated_at = datetime.utcnow()
    await crud.execution.save(execution)

    # Run
    stdout = docker.containers.run(
        image=execution.job.image,
        command=execution.job.command
    )

    # Finish
    execution.stderr = ''
    execution.stdout = stdout
    execution.exit = 0
    execution.finished_at = datetime.utcnow()
    execution.updated_at = datetime.utcnow()
    execution.status = Status.done

    return await crud.execution.save(execution)
