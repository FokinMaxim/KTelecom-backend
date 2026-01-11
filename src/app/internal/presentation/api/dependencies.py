import os

from fastapi import Depends
from sqlalchemy.orm import Session

from src.app.internal.data.repositories.user_repository import UserRepository
from src.app.internal.domain.services.notification_service import NotificationService
from src.app.internal.notifications.email_sender import EmailSender
from src.app.internal.notifications.telegram_sender import TelegramAiogramChannel
from src.config.database import get_db

from src.app.internal.data.repositories.comment_repository import CommentRepository
from src.app.internal.data.repositories.queue_repository import QueueRepository
from src.app.internal.data.repositories.record_repository import RecordRepository
from src.app.internal.domain.services.s3_service import S3StorageService
from src.app.internal.data.repositories.attachment_repository import AttachmentRepository
from dotenv import load_dotenv

from typing import Optional


load_dotenv()
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def get_comment_repository(db: Session = Depends(get_db)):
    return CommentRepository(db)


def get_queue_repository(db: Session = Depends(get_db)):
    return QueueRepository(db)


def get_record_repository(db: Session = Depends(get_db)):
    return RecordRepository(db)

def get_attachment_repository(
    db: Session = Depends(get_db),
) -> AttachmentRepository:
    return AttachmentRepository(
        db=db,
        record_repo=RecordRepository(db),
        s3_service=S3StorageService(),
    )

def get_user_repository(db: Session = Depends(get_db),) -> UserRepository:
    return UserRepository(db)

def get_email_sender() -> EmailSender:
    """
    EmailSender — stateless, можно создавать на каждый запрос
    """
    return EmailSender(
        host=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER,
        password=SMTP_PASSWORD,
        from_email=SMTP_FROM,
    )


def get_telegram_channel() -> Optional[TelegramAiogramChannel]:
    """Возвращает TelegramChannel, если настроен токен бота"""
    if not TELEGRAM_BOT_TOKEN:
        print("⚠️ Telegram bot token not configured, Telegram notifications disabled")
        return None

    try:
        channel = TelegramAiogramChannel(
            bot_token=TELEGRAM_BOT_TOKEN
        )
        print("✅ Telegram channel initialized")
        return channel
    except Exception as e:
        print(f"❌ Failed to initialize Telegram channel: {e}")
        return None


def get_notification_service(
    user_repository: UserRepository = Depends(get_user_repository),
    email_sender: EmailSender = Depends(get_email_sender),
    telegram_channel: TelegramAiogramChannel | None = Depends(get_telegram_channel),
) -> NotificationService:
    return NotificationService(
        email_sender=email_sender,
        user_repository=user_repository,
        telegram_channel=telegram_channel,
    )