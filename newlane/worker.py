from datetime import datetime

import bson

from newlane.models import Execution, Status
from newlane.settings.db import db
from newlane.settings.docker import client


async def run_container(id: str, image: str, command: str):
    id = bson.ObjectId(id)
    execution = await db.find_one(Execution, Execution.id == id)

    # Start
    execution.started_at = datetime.utcnow()
    execution.status = Status.running
    await db.save(execution)
    
    # Run
    stdout = client.containers.run(image=image, command=command)
    
    # Finish
    execution.error = ''
    execution.log = stdout
    execution.exit_code = 0
    execution.finished_at = datetime.utcnow()
    execution.status = Status.done
    await db.save(execution)

    return execution
