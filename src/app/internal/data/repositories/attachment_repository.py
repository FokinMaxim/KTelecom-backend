from uuid import UUID
from fastapi import UploadFile
from src.app.internal.domain.entities.attachment_entity import AttachmentEntity
from src.app.internal.domain.interfaces.record_interface import IRecordRepository
from src.app.internal.domain.interfaces.attachment_interface import IAttachmentRepository
from src.app.internal.domain.services.s3_service import S3StorageService
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from src.app.internal.data.models.attachment_model import AttachmentModel



class UploadAttachmentUseCase:
    def __init__(
        self,
        record_repo: IRecordRepository,
        attachment_repo: IAttachmentRepository,
        s3_service: S3StorageService,
    ):
        self.record_repo = record_repo
        self.attachment_repo = attachment_repo
        self.s3_service = s3_service

    async def execute(
        self,
        record_id: UUID,
        file: UploadFile,
    ) -> AttachmentEntity:
        record = await self.record_repo.get_record(record_id)
        if not record:
            raise ValueError("Record not found")

        object_key = self.s3_service.generate_object_key(
            record_id=str(record_id),
            filename=file.filename,
        )

        await self.s3_service.upload_file(
            file=file,
            object_key=object_key,
        )

        attachment = AttachmentEntity(
            record_id=record_id,
            object_key=object_key,
            filename=file.filename,
            content_type=file.content_type,
            size=file.size,
        )

        return await self.attachment_repo.create(attachment)


class DetachAttachmentUseCase:
    def __init__(
        self,
        attachment_repo: IAttachmentRepository,
        s3_service: S3StorageService,
    ):
        self.attachment_repo = attachment_repo
        self.s3_service = s3_service

    async def execute(self, attachment_id: UUID) -> None:
        attachment = await self.attachment_repo.get_by_id(attachment_id)
        if not attachment:
            raise ValueError("Attachment not found")

        await self.s3_service.delete_file(attachment.object_key)
        await self.attachment_repo.delete(attachment_id)


class AttachmentRepository(IAttachmentRepository):
    def __init__(self, db: Session):
        self.db = db

    async def create(self, attachment: AttachmentEntity) -> AttachmentEntity:
        db_attachment = AttachmentModel(**attachment.dict())
        self.db.add(db_attachment)
        self.db.commit()
        self.db.refresh(db_attachment)
        return AttachmentEntity.from_orm(db_attachment)

    async def get_by_id(self, attachment_id: UUID) -> Optional[AttachmentEntity]:
        attachment = (
            self.db.query(AttachmentModel)
            .filter(AttachmentModel.attachment_id == attachment_id)
            .first()
        )
        return AttachmentEntity.from_orm(attachment) if attachment else None

    async def get_by_record(self, record_id: UUID) -> List[AttachmentEntity]:
        attachments = (
            self.db.query(AttachmentModel)
            .filter(AttachmentModel.record_id == record_id)
            .all()
        )
        return [AttachmentEntity.from_orm(a) for a in attachments]

    async def delete(self, attachment_id: UUID) -> bool:
        attachment = (
            self.db.query(AttachmentModel)
            .filter(AttachmentModel.attachment_id == attachment_id)
            .first()
        )
        if not attachment:
            return False

        self.db.delete(attachment)
        self.db.commit()
        return True
