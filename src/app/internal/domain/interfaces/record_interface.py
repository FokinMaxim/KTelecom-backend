from abc import ABC, abstractmethod
from uuid import UUID
from typing import List, Optional

from src.app.internal.domain.entities.record_entity import RecordEntity


class IRecordRepository(ABC):

    @abstractmethod
    async def create_record(self, record: RecordEntity) -> RecordEntity:
        pass

    @abstractmethod
    async def get_record(self, record_id: UUID) -> Optional[RecordEntity]:
        pass

    @abstractmethod
    async def get_records_by_queue(self, queue_id: UUID) -> List[RecordEntity]:
        pass

    @abstractmethod
    async def get_records_by_user(self, user_id: UUID) -> List[RecordEntity]:
        pass

    @abstractmethod
    async def delete_record(self, record_id: UUID) -> bool:
        pass

    @abstractmethod
    async def update_record_partial(
        self,
        record_id: UUID,
        update_data: dict
    ) -> Optional[RecordEntity]:
        pass
