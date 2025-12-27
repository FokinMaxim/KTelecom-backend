from fastapi import APIRouter, Depends, HTTPException, UploadFile, status, File
from uuid import UUID
from typing import List

from src.app.internal.presentation.api.auth_controller import get_current_user
from src.app.internal.domain.entities.user_entity import UserEntity
from src.app.internal.domain.entities.attachment_entity import AttachmentEntity
from src.app.internal.data.repositories.attachment_repository import AttachmentRepository
from src.app.internal.data.repositories.record_repository import RecordRepository
from src.app.internal.data.repositories.queue_repository import QueueRepository
from .dependencies import get_attachment_repository, get_queue_repository, get_record_repository
from ..scheme.attachment_scheme import *

router = APIRouter(prefix="/attachments", tags=["attachments"])


# =========================
# Helper function
# =========================
async def check_attachment_permissions(
        *,
        record_id: UUID,
        current_user: UserEntity,
        record_repo: RecordRepository,
        queue_repo: QueueRepository,
):
    record = await record_repo.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    queue = await queue_repo.get_queue(record.queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")

    is_record_owner = record.user_id == current_user.uuid
    is_queue_owner = queue.owner_id == current_user.uuid

    if not (is_record_owner or is_queue_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage attachments for this record",
        )

    return record


# =========================
# Routes
# =========================
@router.post(
    "/record/{record_id}",
    response_model=AttachmentEntity,
    status_code=status.HTTP_201_CREATED,
)
async def attach_file_to_record(
        record_id: UUID,
        file: UploadFile = File(...),
        current_user: UserEntity = Depends(get_current_user),
        attachment_repo: AttachmentRepository = Depends(get_attachment_repository),
        record_repo: RecordRepository = Depends(get_record_repository),
        queue_repo: QueueRepository = Depends(get_queue_repository),
):
    await check_attachment_permissions(
        record_id=record_id,
        current_user=current_user,
        record_repo=record_repo,
        queue_repo=queue_repo,
    )

    return await attachment_repo.attach_file(
        record_id=record_id,
        file=file,
    )


@router.get(
    "/record/{record_id}",
    response_model=List[AttachmentResponse],
    status_code=status.HTTP_200_OK,
)
async def get_record_attachments(
        record_id: UUID,
        current_user: UserEntity = Depends(get_current_user),
        attachment_repo: AttachmentRepository = Depends(get_attachment_repository),
        record_repo: RecordRepository = Depends(get_record_repository),
        queue_repo: QueueRepository = Depends(get_queue_repository),
):
    # Проверяем права доступа
    await check_attachment_permissions(
        record_id=record_id,
        current_user=current_user,
        record_repo=record_repo,
        queue_repo=queue_repo,
    )

    # Получаем все вложения для записи
    attachments = await attachment_repo.get_by_record(record_id)

    # Генерируем ссылки для скачивания для каждого вложения
    result = []
    for attachment in attachments:
        download_url = await attachment_repo.get_download_url(
            attachment_id=attachment.attachment_id
        )

        result.append(AttachmentResponse(
            attachment_id=attachment.attachment_id,
            record_id=attachment.record_id,
            original_filename=attachment.original_filename,
            created_at=attachment.created_at,
            download_url=download_url,
        ))

    return result


@router.delete(
    "/{attachment_id}",
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
)
async def detach_file(
        attachment_id: UUID,
        current_user: UserEntity = Depends(get_current_user),
        attachment_repo: AttachmentRepository = Depends(get_attachment_repository),
        record_repo: RecordRepository = Depends(get_record_repository),
        queue_repo: QueueRepository = Depends(get_queue_repository),
):
    attachment = await attachment_repo.get_by_id(attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    await check_attachment_permissions(
        record_id=attachment.record_id,
        current_user=current_user,
        record_repo=record_repo,
        queue_repo=queue_repo,
    )

    await attachment_repo.detach(attachment_id)

    return DeleteResponse(message="Attachment deleted successfully")
