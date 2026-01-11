from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import List

from src.app.internal.data.repositories.record_repository import RecordRepository
from src.app.internal.data.repositories.queue_repository import QueueRepository
from src.app.internal.presentation.scheme.record_schema import (
    RecordCreate,
    RecordUpdate,
    RecordResponse, RecordStatusUpdate,
)
from src.app.internal.presentation.api.auth_controller import get_current_user
from src.app.internal.domain.entities.user_entity import UserEntity
from src.app.internal.domain.entities.record_entity import RecordEntity, RecordReschedule
from src.app.internal.domain.services.notification_service import NotificationService
from .dependencies import get_queue_repository, get_record_repository, get_notification_service

router = APIRouter(prefix="/records", tags=["records"])


@router.post("/", response_model=RecordResponse, status_code=status.HTTP_201_CREATED)
async def create_record(
    record_create: RecordCreate,
    current_user: UserEntity = Depends(get_current_user),
    record_repo: RecordRepository = Depends(get_record_repository),
    queue_repo: QueueRepository = Depends(get_queue_repository),
    notification_service: NotificationService = Depends(get_notification_service),
):
    queue = await queue_repo.get_queue(record_create.queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")

    has_collision = await record_repo.has_time_collision(
        queue_id=queue.queue_id,
        meeting_datetime=record_create.meeting_datetime,
        interval=queue.record_interval,
    )

    if has_collision:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Record time collides with another record"
        )


    record_entity = RecordEntity(
        user_id=current_user.uuid,
        queue_id=record_create.queue_id,
        purpose=record_create.purpose,
        meeting_datetime=record_create.meeting_datetime,
        urgency_level=record_create.urgency_level,
    )

    new_record = await record_repo.create_record(record_entity)

    # Уведомляем владельца очереди
    if queue.owner_id != current_user.uuid:
        await notification_service.notify_queue_owner_record_created(
            record=new_record,
            queue_owner_id=queue.owner_id,
        )

    return new_record


@router.get("/queue/{queue_id}", response_model=List[RecordResponse])
async def get_records_by_queue(
    queue_id: UUID,
    record_repo: RecordRepository = Depends(get_record_repository),
):
    return await record_repo.get_records_by_queue(queue_id)


@router.get("/me", response_model=List[RecordResponse])
async def get_my_records(
    current_user: UserEntity = Depends(get_current_user),
    record_repo: RecordRepository = Depends(get_record_repository),
):
    return await record_repo.get_records_by_user(current_user.uuid)


@router.patch("/{record_id}", response_model=RecordResponse)
async def update_record(
    record_id: UUID,
    record_update: RecordUpdate,
    current_user: UserEntity = Depends(get_current_user),
    record_repo: RecordRepository = Depends(get_record_repository),
    queue_repo: QueueRepository = Depends(get_queue_repository),
):

    old_record = await record_repo.get_record(record_id)
    if not old_record:
        raise HTTPException(status_code=404, detail="Record not found")

    queue = await queue_repo.get_queue(old_record.queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")

    # 3. Проверка прав
    is_record_owner = old_record.user_id == current_user.uuid
    is_queue_owner = queue.owner_id == current_user.uuid

    if not (is_record_owner or is_queue_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this record"
        )
    update_data = record_update.dict(exclude_unset=True)

    result = await record_repo.update_record_partial(
        record_id=record_id,
        update_data=update_data,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Record not found")

    new_record, status_changed = result

    return new_record


@router.delete("/{record_id}", status_code=status.HTTP_200_OK)
async def delete_record(
    record_id: UUID,
    current_user: UserEntity = Depends(get_current_user),
    record_repo: RecordRepository = Depends(get_record_repository),
    queue_repo: QueueRepository = Depends(get_queue_repository),
):
    record = await record_repo.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    queue = await queue_repo.get_queue(record.queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")

    if (
        record.user_id != current_user.uuid
        and queue.owner_id != current_user.uuid
    ):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to delete this record"
        )

    success = await record_repo.delete_record(record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Record not found")

    return {"message": "Record deleted successfully"}


@router.patch("/{record_id}/status", response_model=RecordResponse)
async def update_record_status(
        record_id: UUID,
        status_update: RecordStatusUpdate,
        current_user: UserEntity = Depends(get_current_user),
        record_repo: RecordRepository = Depends(get_record_repository),
        queue_repo: QueueRepository = Depends(get_queue_repository),
        notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Отдельный хендлер для обновления статуса заявки
    Только владелец очереди может менять статус
    """
    old_record = await record_repo.get_record(record_id)
    if not old_record:
        raise HTTPException(status_code=404, detail="Record not found")

    queue = await queue_repo.get_queue(old_record.queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")

    # Проверка прав - только владелец очереди может менять статус
    if queue.owner_id != current_user.uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only queue owner can change record status"
        )

    # Проверяем, изменился ли статус
    if old_record.status == status_update.status:
        return old_record  # Статус не изменился, возвращаем текущую запись

    update_data = {"status": status_update.status}

    result = await record_repo.update_record_partial(
        record_id=record_id,
        update_data=update_data,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Record not found")

    new_record, status_changed = result

    # Отправляем уведомление об изменении статуса
    if status_changed:
        await notification_service.notify_record_status_changed(
            old_record=old_record,
            new_record=new_record,
        )

    return new_record


@router.patch(
    "/{record_id}/reschedule",
    response_model=RecordResponse,
)
async def reschedule_record(
    record_id: UUID,
    data: RecordReschedule,
    current_user: UserEntity = Depends(get_current_user),
    record_repo: RecordRepository = Depends(get_record_repository),
    queue_repo: QueueRepository = Depends(get_queue_repository),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Перенос времени записи.
    Доступно только владельцу очереди.
    """

    # 1. Получаем запись
    old_record = await record_repo.get_record(record_id)
    if not old_record:
        raise HTTPException(status_code=404, detail="Record not found")

    # 2. Получаем очередь
    queue = await queue_repo.get_queue(old_record.queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")

    # 3. Проверка прав
    if queue.owner_id != current_user.uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only queue owner can reschedule record"
        )

    # 4. Если время не изменилось — ничего не делаем
    if old_record.meeting_datetime == data.meeting_datetime:
        return old_record

    # 5. Обновляем запись
    result = await record_repo.update_record_partial(
        record_id=record_id,
        update_data={
            "meeting_datetime": data.meeting_datetime,
            "meeting_notification_sent": False,
        }
    )

    if not result:
        raise HTTPException(status_code=404, detail="Record not found")

    new_record, _ = result

    print(new_record.user_id, new_record.meeting_datetime)
    # 6. Уведомляем владельца записи
    await notification_service.notify_record_rescheduled(
        old_record=old_record,
        new_record=new_record,
    )

    return new_record