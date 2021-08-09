from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor

from newlane import core
from newlane import models
from newlane.api import router
import newlane.tracing  # noqa


app = FastAPI()
app.include_router(router)
app.add_middleware(GZipMiddleware)

FastAPIInstrumentor.instrument_app(app)
PymongoInstrumentor().instrument()
RedisInstrumentor().instrument()


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
