from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, ForeignKey, Enum, Interval
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.config.database import Base
import uuid
import enum


class UrgencyLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Status(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class RecordModel(Base):
    __tablename__ = "records"

    record_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=False, index=True)
    queue_id = Column(UUID(as_uuid=True), ForeignKey("queues.queue_id"), nullable=False, index=True)
    purpose = Column(Text, nullable=False)
    meeting_datetime = Column(DateTime, nullable=False)
    urgency_level = Column(Enum(UrgencyLevel), nullable=False, default=UrgencyLevel.MEDIUM)
    status = Column(Enum(Status), nullable=False, default=Status.PENDING)
    manager_comment = Column(Text, nullable=True)

    # Relationships
    user = relationship("UserModel", back_populates="records")
    queue = relationship("QueueModel", back_populates="records")
    attachments = relationship("AttachmentModel", back_populates="record", lazy="selectin")
