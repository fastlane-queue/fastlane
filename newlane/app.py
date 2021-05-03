from fastapi import FastAPI
from pydantic import BaseModel
from redis.utils import pipeline
from starlette import status
from starlette.responses import JSONResponse

from .api import router

app = FastAPI()
app.include_router(router, prefix='/tasks')