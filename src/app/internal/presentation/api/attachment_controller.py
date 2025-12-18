from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session
from uuid import UUID

from src.config.database import get_db
from src.app.internal.presentation.scheme.attachment_schema import AttachmentResponse
from src.app.internal.data.repositories.attachment_repository import UploadAttachmentUseCase, DetachAttachmentUseCase
from src.app.internal.data.repositories.record_repository import RecordRepository
from src.app.internal.data.repositories.attachment_repository import AttachmentRepository
from src.app.internal.domain.services.s3_service import S3StorageService

router = APIRouter(prefix="/attachments", tags=["attachments"])


def get_upload_use_case(db: Session = Depends(get_db)) -> UploadAttachmentUseCase:
    return UploadAttachmentUseCase(
        record_repo=RecordRepository(db),
        attachment_repo=AttachmentRepository(db),
        s3_service=S3StorageService(),
    )


def get_detach_use_case(db: Session = Depends(get_db)) -> DetachAttachmentUseCase:
    return DetachAttachmentUseCase(
        attachment_repo=AttachmentRepository(db),
        s3_service=S3StorageService(),
    )


@router.post(
    "/records/{record_id}",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment(
    record_id: UUID,
    file: UploadFile = File(...),
    use_case: UploadAttachmentUseCase = Depends(get_upload_use_case),
):
    try:
        return await use_case.execute(record_id, file)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def detach_attachment(
    attachment_id: UUID,
    use_case: DetachAttachmentUseCase = Depends(get_detach_use_case),
):
    try:
        await use_case.execute(attachment_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )