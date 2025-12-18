from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class AttachmentEntity(BaseModel):
    attachment_id: UUID
    object_key: str
    filename: str
    content_type: str
    created_at: datetime

    class Config:
        from_attributes = True
