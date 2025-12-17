from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from src.app.internal.data.models.record_model import UrgencyLevel, Status


class RecordCreate(BaseModel):
    queue_id: UUID
    purpose: str
    meeting_datetime: datetime
    urgency_level: Optional[UrgencyLevel] = UrgencyLevel.MEDIUM


class RecordUpdate(BaseModel):
    purpose: Optional[str]
    meeting_datetime: Optional[datetime]
    urgency_level: Optional[UrgencyLevel]
    status: Optional[Status]
    manager_comment: Optional[str]


class RecordResponse(BaseModel):
    record_id: UUID
    user_id: UUID
    queue_id: UUID
    purpose: str
    meeting_datetime: datetime
    urgency_level: UrgencyLevel
    status: Status
    manager_comment: Optional[str]

    class Config:
        orm_mode = True
