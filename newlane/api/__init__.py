from fastapi import APIRouter

router = APIRouter()

# Import routes so they can add themselves
from . import jobs
from . import tasks
from . import executions