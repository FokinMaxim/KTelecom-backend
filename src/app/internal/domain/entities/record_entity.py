from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

from src.app.internal.data.models.record_model import UrgencyLevel, Status


class RecordEntity(BaseModel):
    record_id: Optional[UUID] = None
    user_id: UUID
    queue_id: UUID

    purpose: str
    meeting_datetime: datetime

    urgency_level: UrgencyLevel = UrgencyLevel.MEDIUM
    status: Status = Status.PENDING
    manager_comment: Optional[str] = None

    class Config:
        from_attributes = True
