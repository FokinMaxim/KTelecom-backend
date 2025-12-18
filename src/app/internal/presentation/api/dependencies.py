from fastapi import Depends
from sqlalchemy.orm import Session
from src.config.database import get_db

from src.app.internal.data.repositories.comment_repository import CommentRepository
from src.app.internal.data.repositories.queue_repository import QueueRepository
from src.app.internal.data.repositories.record_repository import RecordRepository


def get_comment_repository(db: Session = Depends(get_db)):
    return CommentRepository(db)


def get_queue_repository(db: Session = Depends(get_db)):
    return QueueRepository(db)


def get_record_repository(db: Session = Depends(get_db)):
    return RecordRepository(db)

