from enum import Enum
from typing import Optional
from uuid import uuid4, UUID
from datetime import datetime

from odmantic import Model, Field, Reference

from .job import Job


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
    id: UUID = Field(primary_field=True, default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified_at: datetime = Field(default_factory=datetime.utcnow)

    job: Job = Reference()

    log: Optional[str]
    error: Optional[str]
    exit_code: Optional[int]
    metadata: dict = {}
    status: Status = Status.enqueued
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
