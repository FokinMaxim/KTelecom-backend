from uuid import uuid4
from datetime import datetime
from src.app.internal.domain.entities.comment_entity import CommentEntity


MAX_COMMENTS = 5


class UpsertCommentUseCase:
    def __init__(
        self,
        record_repo,
        queue_repo,
        comment_repo,
    ):
        self.record_repo = record_repo
        self.queue_repo = queue_repo
        self.comment_repo = comment_repo

    async def execute(
        self,
        *,
        user_id,
        record_id,
        text,
        comment_id=None,
    ):
        record = await self.record_repo.get_record(record_id)
        if record is None:
            raise ValueError("Record not found")

        queue = await self.queue_repo.get_queue(record.queue_id)
        if queue is None:
            raise ValueError("Queue not found")

        if queue.owner_id != user_id:
            raise PermissionError("User is not owner of queue")

        if comment_id is None:
            now = datetime.utcnow()
            comment = CommentEntity(
                comment_id=uuid4(),
                queue_id=queue.queue_id,
                record_id=record.record_id,
                text=text,
                created_at=now,
                last_used_at=now,
            )

            await self.comment_repo.create_comment(comment)

            count = await self.comment_repo.count_comments_by_queue(queue.queue_id)
            if count > MAX_COMMENTS:
                await self.comment_repo.delete_oldest_comments(
                    queue_id=queue.queue_id,
                    limit=MAX_COMMENTS,
                )

            await self.record_repo.update_record_partial(
                record_id=record.record_id,
                update_data={"manager_comment": text}
            )
            print(text)
            return

        comment = await self.comment_repo.get_comment(comment_id)
        if comment is None:
            raise ValueError("Comment not found")

        if comment.queue_id != queue.queue_id:
            raise PermissionError("Comment does not belong to this queue")

        comment.text = text
        comment.last_used_at = datetime.utcnow()

        await self.comment_repo.update_comment(comment_id, comment)

        await self.record_repo.update_record_partial(
            record_id=record.record_id,
            update_data={"manager_comment": text}
        )
        print(text)