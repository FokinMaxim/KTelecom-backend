from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class AttachmentEntity(BaseModel):
    attachment_id: UUID
    record_id: UUID
    object_key: str
    original_filename: str
    created_at: datetime

    class Config:
        from_attributes = True