from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.config.database import Base
import uuid



class UserModel(Base):
    __tablename__ = "users"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    login = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    email_notifications = Column(Boolean, nullable=False, default=False)
    telegram_login = Column(String(50), unique=True, nullable=True)
    telegram_notifications = Column(Boolean, nullable=False, default=False)

    # Relationships
    refresh_tokens = relationship("RefreshTokenModel", back_populates="user", lazy="selectin")
    queues_owned = relationship("QueueModel", back_populates="owner", lazy="selectin")
    #records = relationship("RecordModel", back_populates="user", lazy="selectin")

