class GetQueueCommentsUseCase:

    def __init__(self, queue_repo, comment_repo):
        self.queue_repo = queue_repo
        self.comment_repo = comment_repo

    async def execute(self, user_id, queue_id):
        queue = await self.queue_repo.get_queue(queue_id)
        if queue is None:
            raise ValueError("Queue not found")

        if queue.owner_id != user_id:
            raise PermissionError("Queue does not belong to user")

        return await self.comment_repo.get_by_queue(queue_id)