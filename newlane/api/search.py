from fastapi import APIRouter

from newlane.models import Task
from newlane.core import db

router = APIRouter(prefix='/search')


@router.get('/')
async def get_search(query: str, page: int = 1) -> dict:
    PAGE_SIZE = 10

    total = await db.count(Task, Task.name == query)
    tasks = await db.find(Task, skip=(page - 1) * PAGE_SIZE, limit=PAGE_SIZE)

    return {
        'hasNext': page * PAGE_SIZE < total,
        'hasPrev': (page - 1) * PAGE_SIZE > 0,
        'items': tasks,
        'nextUrl': 'TODO',
        'page': page,
        'pages': math.ceil(total / PAGE_SIZE),
        'perPage': PAGE_SIZE,
        'prevUrl': 'TODO',
        'total': total
    }
