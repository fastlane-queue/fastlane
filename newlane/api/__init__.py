from fastapi import APIRouter

from .tasks import router as tasks_router
from .search import router as search_router

router = APIRouter()
router.include_router(tasks_router)
router.include_router(search_router)
