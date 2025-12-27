from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class AttachmentResponse(BaseModel):
    attachment_id: UUID
    record_id: UUID
    original_filename: str
    created_at: datetime
    download_url: str

    class Config:
        from_attributes = True


class QueueAttachmentResponse(BaseModel):
    attachment_id: UUID
    record_id: UUID
    original_filename: str
    created_at: datetime
    download_url: str


class DeleteResponse(BaseModel):
    message: str
