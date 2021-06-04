from fastapi import FastAPI

from newlane import core
from newlane import models
from newlane.api import router

app = FastAPI()
app.include_router(router)


@app.on_event('startup')
async def startup():
    db = core.get_db()

    task = db.get_collection(models.Task)
    await task.create_index('name', unique=True)
    await task.create_index([('name', 1), ('updated_at', -1)])
    await task.create_index([('name', 1), ('created_at', -1)])

    job = db.get_collection(models.Job)
    await job.create_index([('task', 1), ('created_at', -1)])
    await job.create_index([('task', 1), ('updated_at', -1)])

    execution = db.get_collection(models.Execution)
    await execution.create_index([('job', 1), ('updated_at', -1)])
    await execution.create_index([('job', 1), ('created_at', -1)])
