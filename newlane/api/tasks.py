from fastapi import APIRouter

from newlane import crud
from newlane.api import payloads


router = APIRouter(prefix='/tasks')


@router.post('/', status_code=201)
async def post_task(body: payloads.Task) -> dict:
    return await crud.task.get_or_create(name=body.name)


@router.get('/')
async def get_tasks(page: int = 1, size: int = 10) -> dict:
    return await crud.task.page(page=page, size=size)


@router.get('/{task}/')
async def get_task(task: str) -> dict:
    return await crud.task.get_or_404(name=task)


@router.delete('/{task}/')
async def delete_task(task: str) -> dict:
    task = await crud.task.get_or_404(name=task)
    return await crud.task.remove(task)
