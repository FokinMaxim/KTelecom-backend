from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from src.app.internal.data.models.record_model import UrgencyLevel, Status
from src.app.internal.domain.entities.attachment_entity import AttachmentEntity

class RecordEntity(BaseModel):
    record_id: UUID
    user_id: UUID
    queue_id: UUID
    purpose: str
    meeting_datetime: datetime
    urgency_level: UrgencyLevel
    status: Status
    manager_comment: Optional[str]

    attachments: List[AttachmentEntity] = []

    class Config:
        from_attributes = True

