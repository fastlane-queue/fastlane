from uuid import uuid4, UUID
from datetime import datetime

from odmantic import Model, Field, Reference

from .task import Task


class Job(Model):
    id: UUID = Field(primary_field=True, default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified_at: datetime = Field(default_factory=datetime.utcnow)

    task: Task = Reference()

    image: str
    command: str
    metadata: dict = {}
    scheduled: bool = False
