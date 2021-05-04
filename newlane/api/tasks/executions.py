from fastapi import APIRouter, Depends
from starlette.responses import PlainTextResponse

from . import router
from newlane.api import deps
from newlane.models import Task, Job, Execution


@router.get('/{task}/jobs/{job}/executions/{exec}')
async def get_task_job_execution(
    execution: Execution = Depends(deps.get_execution)
):
    return execution


@router.get('/{task}/jobs/{job}/executions/{exec}/logs')
async def get_task_job_execution_logs(
    execution: Execution = Depends(deps.get_execution)
):
    return PlainTextResponse(execution.log)


@router.get('/{task}/jobs/{job}/executions/{exec}/stdout')
async def get_task_job_execution_stdout(
    execution: Execution = Depends(deps.get_execution)
):
    return PlainTextResponse(execution.log)


@router.get('/{task}/jobs/{job}/executions/{exec}/stderr')
async def get_task_job_execution_stderr(
    execution: Execution = Depends(deps.get_execution)
):
    return PlainTextResponse(execution.error)


@router.post('/{task}/jobs/{job}/executions/{exec}/stop')
async def post_task_job_execution_stop(task: str, job: str, exec: str):
    raise NotImplementedError()


@router.get('/{task}/jobs/{job}/stream/executions/{exec}')
async def get_task_job_execution_stream(task: str, job: str, exec: str):
    raise NotImplementedError()