from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from src.config.database import get_db
from src.app.internal.data.repositories.record_repository import RecordRepository
from src.app.internal.data.repositories.queue_repository import QueueRepository
from src.app.internal.presentation.scheme.record_schema import (
    RecordCreate,
    RecordUpdate,
    RecordResponse,
)
from src.app.internal.presentation.api.auth_controller import get_current_user
from src.app.internal.domain.entities.user_entity import UserEntity
from src.app.internal.domain.entities.record_entity import RecordEntity

router = APIRouter(prefix="/records", tags=["records"])


def get_record_repository(db: Session = Depends(get_db)) -> RecordRepository:
    return RecordRepository(db)


def get_queue_repository(db: Session = Depends(get_db)) -> QueueRepository:
    return QueueRepository(db)

@router.post("/", response_model=RecordResponse, status_code=status.HTTP_201_CREATED)
async def create_record(
    record_create: RecordCreate,
    current_user: UserEntity = Depends(get_current_user),
    record_repo: RecordRepository = Depends(get_record_repository),
    queue_repo: QueueRepository = Depends(get_queue_repository),
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
        user_id=current_user.uuid,  # ✅ from token
        queue_id=record_create.queue_id,
        purpose=record_create.purpose,
        meeting_datetime=record_create.meeting_datetime,
        urgency_level=record_create.urgency_level,
    )

    return await record_repo.create_record(record_entity)


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
            detail="You don't have permission to update this record"
        )

    update_data = record_update.dict(exclude_unset=True)
    updated = await record_repo.update_record_partial(record_id, update_data)

    return updated


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