from enum import Enum
from typing import Optional
from uuid import uuid4, UUID
from datetime import datetime

from odmantic import Model, Field, Reference, EmbeddedModel

from .job import Job


class Status(str, Enum):
    done = 'done'
    failed = 'failed'
    expired = 'expired'
    pulling = 'pulling'
    pulled = 'pulled'
    running = 'running'
    stopped = 'stopped'
    enqueued = 'enqueued'
    timedout = 'timedout'


class Message(EmbeddedModel):
    id: Optional[UUID]


class Execution(Model):
    id: UUID = Field(primary_field=True, default_factory=uuid4)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    job: Job = Reference()

    exit: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]
    status: Status = Status.enqueued

    started_at: Optional[datetime]
    finished_at: Optional[datetime]

    message: Message = Field(default_factory=Message)
