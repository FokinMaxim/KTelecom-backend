from sqlalchemy import Column, ForeignKey, Interval
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.config.database import Base
import uuid


class QueueModel(Base):
    __tablename__ = "queues"

    queue_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=False, index=True)
    cleanup_interval = Column(Interval, nullable=False, default="1 day")
    record_interval = Column(Interval, nullable=False, default="30 minutes")

    # Relationships
    owner = relationship("UserModel", back_populates="queues_owned")
    comments = relationship("CommentModel", back_populates="queue")
    records = relationship("RecordModel", back_populates="queue")