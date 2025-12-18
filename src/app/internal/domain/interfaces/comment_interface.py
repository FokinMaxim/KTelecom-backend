from abc import ABC, abstractmethod
from uuid import UUID
from typing import List, Optional
from src.app.internal.domain.entities.comment_entity import CommentEntity


class ICommentRepository(ABC):

    @abstractmethod
    async def create_comment(self, comment: CommentEntity) -> CommentEntity:
        ...

    @abstractmethod
    async def get_comment(self, comment_id: UUID) -> Optional[CommentEntity]:
        ...

    @abstractmethod
    async def get_by_queue(self, queue_id: UUID) -> List[CommentEntity]:
        ...

    @abstractmethod
    async def count_comments_by_queue(self, queue_id: UUID) -> int:
        ...

    @abstractmethod
    async def delete_oldest_comments(
        self,
        queue_id: UUID,
        limit: int,
    ) -> None:
        ...

    @abstractmethod
    async def update_comment(
        self,
        comment_id: UUID,
        comment: CommentEntity,
    ) -> Optional[CommentEntity]:
        ...
