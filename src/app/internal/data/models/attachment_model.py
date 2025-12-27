from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from src.config.database import Base
from sqlalchemy.orm import relationship


class AttachmentModel(Base):
    __tablename__ = "attachments"

    attachment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    record_id = Column(
        UUID(as_uuid=True),
        ForeignKey("records.record_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    object_key = Column(String(512), nullable=False, unique=True)
    original_filename = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    record = relationship("RecordModel", back_populates="attachments")