from fastapi import Depends
from sqlalchemy.orm import Session
from src.config.database import get_db

from src.app.internal.data.repositories.comment_repository import CommentRepository
from src.app.internal.data.repositories.queue_repository import QueueRepository
from src.app.internal.data.repositories.record_repository import RecordRepository
from src.app.internal.domain.services.s3_service import S3StorageService
from src.app.internal.data.repositories.attachment_repository import AttachmentRepository


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