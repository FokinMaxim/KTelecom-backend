from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from fastapi import UploadFile

from src.app.internal.domain.entities.attachment_entity import AttachmentEntity


class IAttachmentRepository(ABC):

    @abstractmethod
    async def attach_file(self, *, record_id: UUID, file: UploadFile,) -> AttachmentEntity:
        pass

    @abstractmethod
    async def get_by_id(self, attachment_id: UUID,) -> Optional[AttachmentEntity]:
        pass

    @abstractmethod
    async def get_by_record( self, record_id: UUID,) -> List[AttachmentEntity]:
        pass

    @abstractmethod
    async def detach(self, attachment_id: UUID,) -> None:
        pass

    @abstractmethod
    async def get_download_url(self, *, attachment_id: UUID, expires: int = 3600,) -> str:
        pass
