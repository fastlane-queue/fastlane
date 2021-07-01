import sys
from typing import List
from datetime import timedelta

import croniter
from pydantic import BaseModel, validator


class Task(BaseModel):
    name: str


class Job(BaseModel):
    image: str
    command: str
    environment: dict = {}
    cron: str = None
    start_in: timedelta = None
    # metadata: dict = {}
    # notify: dict = {}
    # webhooks: dict = {}
    # retries: int = 0
    # expiration: int = sys.maxsize
    # timeout: int = sys.maxsize

    @validator('cron')
    def validate_cron(cls, v) -> str:
        try:
            croniter.croniter(v)
            return v
        except Exception as e:
            raise ValueError(e)


class Execution(BaseModel):
    start_in: int = 1  # Seconds
