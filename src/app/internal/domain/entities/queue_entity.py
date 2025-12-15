from pydantic import BaseModel, Field
from uuid import UUID
from datetime import timedelta
from typing import Optional

class QueueEntity(BaseModel):
    queue_id: Optional[UUID] = None
    name: str = Field(..., max_length=50)
    owner_id: UUID
    cleanup_interval: timedelta = Field(default=timedelta(days=1))
    record_interval: timedelta = Field(default=timedelta(minutes=30))


    class Config:
        from_attributes = True
