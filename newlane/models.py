from enum import Enum, auto
from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from odmantic import Model, Field, Reference


class Task(Model):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified_at: datetime = Field(default_factory=datetime.utcnow)

    name: str


class Job(Model):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified_at: datetime = Field(default_factory=datetime.utcnow)

    task: Task = Reference()
    
    image: str
    command: str
    metadata: dict = {}
    scheduled: bool = False


class Status(str, Enum):
    done = 'done'
    failed = 'failed'
    expired = 'expired'
    pulling = 'pulling'
    running = 'running'
    stopped = 'stopped'
    enqueued = 'enqueued'
    timedout = 'timedout'


class Execution(Model):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime]
    finished_at: Optional[datetime]

    job: Job = Reference()
    
    log: str = ''
    error: str = ''
    exit_code: int = 0  
    metadata: dict = {}
    status: Status = Status.enqueued
