from fastapi import APIRouter

router = APIRouter(prefix='/tasks')

from . import jobs
from . import tasks
from . import executions
