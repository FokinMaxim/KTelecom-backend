from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from src.config.database import get_db
from src.app.internal.data.repositories.queue_repository import QueueRepository
from src.app.internal.domain.entities.queue_entity import QueueEntity
from src.app.internal.presentation.scheme.queue_schema import (
    QueueCreate, QueueUpdate, QueueResponse
)
from src.app.internal.presentation.api.auth_controller import get_current_user
from src.app.internal.domain.entities.user_entity import UserEntity

router = APIRouter(prefix="/queues", tags=["queues"])


def get_queue_repository(db: Session = Depends(get_db)) -> QueueRepository:
    return QueueRepository(db)


@router.post("/", response_model=QueueResponse, status_code=status.HTTP_201_CREATED)
async def create_queue(
        queue_create: QueueCreate,
        current_user: UserEntity = Depends(get_current_user),
        queue_repo: QueueRepository = Depends(get_queue_repository)):
    """
    Создание новой очереди.
    Владелец очереди определяется из auth токена текущего пользователя.
    """
    # Проверка уникальности имени очереди
    existing_queue = await queue_repo.get_queue_by_name(queue_create.name)
    if existing_queue:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Queue with this name already exists"
        )

    # Создание сущности очереди
    queue_entity = QueueEntity(
        name=queue_create.name,
        owner_id=current_user.uuid,
        cleanup_interval=queue_create.cleanup_interval,
        record_interval=queue_create.record_interval
    )

    # Сохранение в базу
    created_queue = await queue_repo.create_queue(queue_entity)

    return created_queue


@router.get("/", response_model=List[QueueResponse])
async def get_all_queues(
        queue_repo: QueueRepository = Depends(get_queue_repository)):
    """
    Получение списка всех очередей.
    Доступно всем аутентифицированным пользователям.
    """
    return await queue_repo.get_all_queues()


@router.get("/{queue_id}", response_model=QueueResponse)
async def get_queue(
        queue_id: UUID,
        queue_repo: QueueRepository = Depends(get_queue_repository)):
    """
    Получение информации о конкретной очереди по ID.
    Доступно всем аутентифицированным пользователям.
    """
    queue = await queue_repo.get_queue(queue_id)
    if queue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Queue not found"
        )
    return queue


@router.get("/owner/me", response_model=List[QueueResponse])
async def get_my_queues(
        current_user: UserEntity = Depends(get_current_user),
        queue_repo: QueueRepository = Depends(get_queue_repository)):
    """
    Получение списка очередей текущего пользователя.
    """
    return await queue_repo.get_queues_by_owner(current_user.uuid)


@router.get("/owner/{owner_id}", response_model=List[QueueResponse])
async def get_queues_by_owner(
        owner_id: UUID,
        queue_repo: QueueRepository = Depends(get_queue_repository)):
    """
    Получение списка очередей конкретного пользователя.
    Доступно всем аутентифицированным пользователям.
    """
    return await queue_repo.get_queues_by_owner(owner_id)


@router.patch("/{queue_id}", response_model=QueueResponse)
async def update_queue(
        queue_id: UUID,
        queue_update: QueueUpdate,
        current_user: UserEntity = Depends(get_current_user),
        queue_repo: QueueRepository = Depends(get_queue_repository)):
    """
    Изменение параметров очереди.
    Доступно только владельцу очереди.
    """
    # Получение очереди
    existing_queue = await queue_repo.get_queue(queue_id)
    if existing_queue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Queue not found"
        )

    # Проверка прав доступа
    if existing_queue.owner_id != current_user.uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this queue"
        )

    # Проверка уникальности имени, если оно меняется
    if queue_update.name and queue_update.name != existing_queue.name:
        queue_with_same_name = await queue_repo.get_queue_by_name(queue_update.name)
        if queue_with_same_name and queue_with_same_name.queue_id != queue_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Queue with this name already exists"
            )

    # Подготовка данных для обновления
    update_data = queue_update.dict(exclude_unset=True)

    # Обновление очереди
    updated_queue = await queue_repo.update_queue_partial(queue_id, update_data)

    if updated_queue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Queue not found"
        )

    return updated_queue


@router.delete("/{queue_id}", status_code=status.HTTP_200_OK)
async def delete_queue(
        queue_id: UUID,
        current_user: UserEntity = Depends(get_current_user),
        queue_repo: QueueRepository = Depends(get_queue_repository)):
    """
    Удаление очереди.
    Доступно только владельцу очереди.
    """
    # Получение очереди
    existing_queue = await queue_repo.get_queue(queue_id)
    if existing_queue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Queue not found"
        )

    # Проверка прав доступа
    if existing_queue.owner_id != current_user.uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this queue"
        )

    # Удаление очереди
    success = await queue_repo.delete_queue(queue_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Queue not found"
        )

    return {"message": "Queue deleted successfully"}