from uuid import uuid4, UUID
from typing import Optional
from datetime import datetime

from odmantic import Model, Field, Reference

from .task import Task


class Job(Model):
    id: UUID = Field(primary_field=True, default_factory=uuid4)

    created_by: Optional[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    task: Task = Reference()

    image: Optional[str]
    command: Optional[str]
    environment: dict = {}

    cron: Optional[str]
    metadata: dict = {}
