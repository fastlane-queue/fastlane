from uuid import UUID
from datetime import datetime

from newlane import crud
from newlane.models import Execution, Status
from newlane.core.docker import docker


async def run_container(id: UUID, image: str, command: str):
    execution = await crud.execution.get(id=id)

    # Start
    execution.started_at = datetime.utcnow()
    execution.status = Status.running
    await crud.execution.save(execution)

    # Run
    stdout = docker.containers.run(image=image, command=command)

    # Finish
    execution.error = ''
    execution.log = stdout
    execution.exit_code = 0
    execution.finished_at = datetime.utcnow()
    execution.status = Status.done

    return await crud.execution.save(execution)
