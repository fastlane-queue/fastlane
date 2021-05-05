from uuid import uuid4, UUID
from typing import Optional
from datetime import datetime

from odmantic import Model, Field, Reference

from .task import Task


class Job(Model):
    id: UUID = Field(primary_field=True, default_factory=uuid4)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    task: Task = Reference()

    image: Optional[str]
    command: Optional[str]
    envs: dict = {}
    metadata: dict = {}
    scheduled: bool = False
    cron: Optional[str]
