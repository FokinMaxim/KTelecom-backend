from pydantic import BaseModel, Field
from uuid import UUID
from datetime import timedelta
from typing import Optional


class QueueCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Unique queue name")
    cleanup_interval: timedelta = Field(default=timedelta(days=1), description="Cleanup interval")
    record_interval: timedelta = Field(default=timedelta(minutes=30), description="Record interval")

class QueueUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="Unique queue name")
    cleanup_interval: Optional[timedelta] = Field(None, description="Cleanup interval")
    record_interval: Optional[timedelta] = Field(None, description="Record interval")

class QueueResponse(BaseModel):
    queue_id: UUID
    name: str
    owner_id: UUID
    cleanup_interval: timedelta
    record_interval: timedelta
