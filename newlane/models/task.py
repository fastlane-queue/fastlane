from datetime import datetime

from odmantic import Model, Field


class Task(Model):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified_at: datetime = Field(default_factory=datetime.utcnow)

    name: str
