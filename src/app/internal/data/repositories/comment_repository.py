from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from typing import List, Optional
from datetime import datetime

from src.app.internal.data.models.comment_model import CommentModel
from src.app.internal.domain.entities.comment_entity import CommentEntity
from src.app.internal.domain.interfaces.comment_interface import ICommentRepository


class CommentRepository(ICommentRepository):
    def __init__(self, db: Session):
        self.db = db

    async def create_comment(self, comment: CommentEntity) -> CommentEntity:
        comment_data = comment.dict(exclude_none=True)

        if 'comment_id' not in comment_data or comment_data['comment_id'] is None:
            comment_data['comment_id'] = uuid4()

        db_comment = CommentModel(**comment_data)
        self.db.add(db_comment)
        self.db.commit()
        self.db.refresh(db_comment)
        return CommentEntity.from_orm(db_comment)

    async def get_comment(self, comment_id: UUID) -> Optional[CommentEntity]:
        db_comment = (
            self.db.query(CommentModel)
            .filter(CommentModel.comment_id == comment_id)
            .first()
        )
        if db_comment:
            return CommentEntity.from_orm(db_comment)
        return None

    async def get_by_queue(self, queue_id: UUID) -> List[CommentEntity]:
        db_comments = (
            self.db.query(CommentModel)
            .filter(CommentModel.queue_id == queue_id)
            .order_by(CommentModel.created_at.asc())
            .all()
        )
        return [CommentEntity.from_orm(c) for c in db_comments]

    async def count_comments_by_queue(self, queue_id: UUID) -> int:
        return (
            self.db.query(CommentModel)
            .filter(CommentModel.queue_id == queue_id)
            .count()
        )

    async def delete_oldest_comments(self, queue_id: UUID, limit: int) -> None:
        db_comments = (
            self.db.query(CommentModel)
            .filter(CommentModel.queue_id == queue_id)
            .order_by(CommentModel.created_at.asc())
            .all()
        )[::-1]

        if len(db_comments) > limit:
            for comment in db_comments[limit:]:
                print(comment.text)
                self.db.delete(comment)

            self.db.commit()

    async def update_comment(
        self,
        comment_id: UUID,
        comment: CommentEntity,
    ) -> Optional[CommentEntity]:
        db_comment = (
            self.db.query(CommentModel)
            .filter(CommentModel.comment_id == comment_id)
            .first()
        )

        if db_comment:
            update_data = comment.dict(exclude_none=True)
            for key, value in update_data.items():
                if hasattr(db_comment, key) and key != "comment_id":
                    setattr(db_comment, key, value)

            db_comment.last_used_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(db_comment)
            return CommentEntity.from_orm(db_comment)

        return None