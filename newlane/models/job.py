from datetime import datetime

from odmantic import Model, Field, Reference

from .task import Task


class Job(Model):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified_at: datetime = Field(default_factory=datetime.utcnow)

    task: Task = Reference()

    image: str
    command: str
    metadata: dict = {}
    scheduled: bool = False
