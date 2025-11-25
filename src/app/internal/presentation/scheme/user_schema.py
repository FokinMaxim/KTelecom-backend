from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional

class UserCreate(BaseModel):
    login: str
    password_hash: str
    email: EmailStr
    email_notifications: bool = True
    telegram_login: Optional[str] = None
    telegram_notifications: bool = False

class UserRegister(BaseModel):
    login: str
    password: str
    email: EmailStr
    email_notifications: bool = False
    telegram_login: Optional[str] = None
    telegram_notifications: bool = False

class UserUpdate(BaseModel):
    login: Optional[str] = None
    password_hash: Optional[str] = None
    email: Optional[EmailStr] = None
    email_notifications: Optional[bool] = None
    telegram_login: Optional[str] = None
    telegram_notifications: Optional[bool] = None

class UserResponse(BaseModel):
    uuid: UUID
    login: str
    email: str
    email_notifications: bool
    telegram_login: Optional[str] = None
    telegram_notifications: bool

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    login: str
    password_hash: str

class UserEmailUpdate(BaseModel):
    email: EmailStr
    email_notifications: Optional[bool] = None

class UserTelegramUpdate(BaseModel):
    telegram_login: str
    telegram_notifications: Optional[bool] = None
