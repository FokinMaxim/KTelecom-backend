from abc import ABC, abstractmethod
from uuid import UUID
from typing import List, Optional
from src.app.internal.domain.entities.queue_entity import QueueEntity

class IQueueRepository(ABC):
    @abstractmethod
    async def create_queue(self, queue: QueueEntity) -> QueueEntity:
        pass

    @abstractmethod
    async def get_queue(self, queue_id: UUID) -> Optional[QueueEntity]:
        pass

    @abstractmethod
    async def get_queue_by_name(self, name: str) -> Optional[QueueEntity]:
        pass

    @abstractmethod
    async def get_queues_by_owner(self, owner_id: UUID) -> List[QueueEntity]:
        pass

    @abstractmethod
    async def get_all_queues(self) -> List[QueueEntity]:
        pass

    @abstractmethod
    async def update_queue(self, queue_id: UUID, queue: QueueEntity) -> Optional[QueueEntity]:
        pass

    @abstractmethod
    async def update_queue_partial(self, queue_id: UUID, update_data: dict) -> Optional[QueueEntity]:
        pass

    @abstractmethod
    async def delete_queue(self, queue_id: UUID) -> bool:
        pass