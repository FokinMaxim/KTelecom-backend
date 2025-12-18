
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class AttachmentResponse(BaseModel):
    attachment_id: UUID
    filename: str
    content_type: str
    created_at: datetime

    class Config:
        from_attributes = True
