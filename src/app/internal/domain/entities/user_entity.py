from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class UserEntity(BaseModel):
    uuid: Optional[UUID] = None
    login: str
    password_hash: str
    email: str
    email_notifications: bool = False
    telegram_login: Optional[str] = None
    telegram_notifications: bool = False

    class Config:
        from_attributes = True