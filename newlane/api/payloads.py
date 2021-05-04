import sys
from typing import List

from pydantic import BaseModel


class Job(BaseModel):
    image: str
    command: str
    envs: dict = {}
    startIn: str = '5s'
    startAt: int = None
    cron: str = None
    metadata: dict = {}
    notify: dict = {}
    webhooks: dict = {}
    retries: int = 0
    expiration: int = sys.maxsize
    timeout: int = sys.maxsize
