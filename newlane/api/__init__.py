from fastapi import APIRouter

from .routes import router as tasks_router

router = APIRouter()
router.include_router(tasks_router)
