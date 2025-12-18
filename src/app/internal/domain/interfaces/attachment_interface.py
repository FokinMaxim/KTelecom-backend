from abc import ABC, abstractmethod
from typing import List
from uuid import UUID
from src.app.internal.domain.entities.attachment_entity import AttachmentEntity


class IAttachmentRepository(ABC):

    @abstractmethod
    async def create(self, attachment: AttachmentEntity) -> AttachmentEntity:
        pass

    @abstractmethod
    async def get_by_record(self, record_id: UUID) -> List[AttachmentEntity]:
        pass
