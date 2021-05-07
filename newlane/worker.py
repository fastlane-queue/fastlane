from uuid import UUID
from datetime import datetime

from newlane import crud
from newlane import core
from newlane.models import Status


async def cron(id: UUID):
    job = await crud.job.get(id=id)

    execution = await crud.execution.create(job=job)
    
    queue = core.get_queue()
    message = queue.enqueue(pull, execution.id)
    execution.message.id = message.id

    return await crud.execution.save(execution)


async def pull(id: UUID):
    execution = await crud.execution.get(id=id)

    # Update status
    execution.updated_at = datetime.utcnow()
    execution.status = Status.pulling
    await crud.execution.save(execution)

    # Pull
    docker = core.get_docker()
    docker.images.pull(execution.job.image)

    # Next
    queue = core.get_queue()
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
    docker = core.get_docker()
    stdout = docker.containers.run(
        image=execution.job.image,
        command=execution.job.command,
        environment=execution.job.environment
    )

    # Finish
    execution.stderr = ''
    execution.stdout = stdout
    execution.exit = 0
    execution.finished_at = datetime.utcnow()
    execution.updated_at = datetime.utcnow()
    execution.status = Status.done

    return await crud.execution.save(execution)
