from uuid import uuid4, UUID
from datetime import datetime

from odmantic import Model, Field


class Task(Model):
    id: UUID = Field(primary_field=True, default_factory=uuid4)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    name: str
