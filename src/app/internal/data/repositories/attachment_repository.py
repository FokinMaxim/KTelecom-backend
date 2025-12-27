from fastapi import UploadFile
from src.app.internal.domain.entities.attachment_entity import AttachmentEntity
from src.app.internal.domain.interfaces.record_interface import IRecordRepository
from src.app.internal.domain.interfaces.attachment_interface import IAttachmentRepository
from src.app.internal.domain.services.s3_service import S3StorageService
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from src.app.internal.data.models.attachment_model import AttachmentModel


class AttachmentRepository(IAttachmentRepository):
    def __init__(
        self,
        db: Session,
        record_repo: IRecordRepository,
        s3_service: S3StorageService,
    ):
        self.db = db
        self.record_repo = record_repo
        self.s3_service = s3_service

    # =========================
    # Create / Upload
    # =========================
    async def attach_file(
        self,
        *,
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

        # upload внутри сервиса
        self.s3_service.upload(
            object_key=object_key,
            file=file.file,
            content_type=file.content_type,
        )

        db_attachment = AttachmentModel(
            record_id=record_id,
            object_key=object_key,
            original_filename=file.filename,
        )

        self.db.add(db_attachment)
        self.db.commit()
        self.db.refresh(db_attachment)

        return AttachmentEntity.from_orm(db_attachment)

    # =========================
    # Read
    # =========================
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
            .order_by(AttachmentModel.created_at)
            .all()
        )
        return [AttachmentEntity.from_orm(a) for a in attachments]

    # =========================
    # Delete
    # =========================
    async def detach(self, attachment_id: UUID) -> None:
        attachment = (
            self.db.query(AttachmentModel)
            .filter(AttachmentModel.attachment_id == attachment_id)
            .first()
        )
        if not attachment:
            raise ValueError("Attachment not found")

        self.s3_service.delete(object_key=attachment.object_key)

        self.db.delete(attachment)
        self.db.commit()

    # =========================
    # Download (presigned URL)
    # =========================
    async def get_download_url(
        self,
        *,
        attachment_id: UUID,
        expires: int = 3600,
    ) -> str:
        attachment = await self.get_by_id(attachment_id)
        if not attachment:
            raise ValueError("Attachment not found")

        return self.s3_service.generate_download_url(
            object_key=attachment.object_key,
            expires=expires,
        )