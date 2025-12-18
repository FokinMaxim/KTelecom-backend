from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CommentEntity(BaseModel):
    comment_id: UUID | None = None
    queue_id: UUID
    record_id: UUID
    text: str
    created_at: datetime
    last_used_at: datetime

    model_config = ConfigDict(from_attributes=True)

    def touch(self):
        self.last_used_at = datetime.utcnow()