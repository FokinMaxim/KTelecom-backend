from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime

class UpsertCommentRequest(BaseModel):
    record_id: UUID
    text: str
    comment_id: UUID | None = None

class CommentResponse(BaseModel):
    id: UUID = Field(..., alias="comment_id")
    record_id: UUID
    text: str
    created_at: datetime
    last_used_at: datetime