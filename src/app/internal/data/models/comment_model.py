from sqlalchemy import Column, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.config.database import Base
import uuid
from datetime import datetime


class CommentModel(Base):
    __tablename__ = "comments"

    comment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    queue_id = Column(UUID(as_uuid=True), ForeignKey("queues.queue_id"), nullable=False, index=True)
    comment_text = Column(Text, nullable=False)
    last_used = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    queue = relationship("QueueModel", back_populates="comments")