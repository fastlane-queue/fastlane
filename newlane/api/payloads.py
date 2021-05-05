import sys
from typing import List

from pydantic import BaseModel


class Task(BaseModel):
    name: str


class Job(BaseModel):
    image: str
    command: str
    envs: dict = {}
    # startIn: str = '1s'
    # startAt: int = None
    # cron: str = None
    # metadata: dict = {}
    # notify: dict = {}
    # webhooks: dict = {}
    # retries: int = 0
    # expiration: int = sys.maxsize
    # timeout: int = sys.maxsize


class Execution(BaseModel):
    start_in: int = 1  # Seconds
