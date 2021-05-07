from fastapi import APIRouter

from . import tasks
from . import jobs
from . import executions

router = APIRouter()
router.include_router(tasks.router)
router.include_router(jobs.router)
router.include_router(executions.router)
