from fastapi import APIRouter

from . import tasks
from . import jobs
from . import executions
from . import status
from . import docker

router = APIRouter()
router.include_router(tasks.router)
router.include_router(jobs.router)
router.include_router(executions.router)
router.include_router(status.router)
router.include_router(docker.router)
