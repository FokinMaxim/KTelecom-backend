from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from typing import List
from src.config.database import get_db
from src.app.internal.data.repositories.user_repository import UserRepository
from src.app.internal.domain.entities.user_entity import UserEntity
from src.app.internal.presentation.scheme.user_schema import (
    UserCreate, UserUpdate, UserResponse, UserLogin,
    UserEmailUpdate, UserTelegramUpdate
)

router = APIRouter(prefix="/users", tags=["users"])


def get_user_repository(db: Session = Depends(get_db)):
    return UserRepository(db)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
        user: UserCreate,
        user_repo: UserRepository = Depends(get_user_repository)
):
    # Check if login already exists
    existing_user = await user_repo.get_user_by_login(user.login)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Login already registered"
        )

    # Check if email already exists
    existing_email = await user_repo.get_user_by_email(user.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user_data = user.dict()
    user_data['uuid'] = uuid4()
    user_entity = UserEntity(**user_data)
    created_user = await user_repo.create_user(user_entity)
    return created_user


@router.get("/{user_uuid}", response_model=UserResponse)
async def get_user(
        user_uuid: UUID,
        user_repo: UserRepository = Depends(get_user_repository)
):
    user = await user_repo.get_user(user_uuid)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.get("/", response_model=List[UserResponse])
async def get_all_users(user_repo: UserRepository = Depends(get_user_repository)):
    return await user_repo.get_all_users()


@router.get("/by-login/{login}", response_model=UserResponse)
async def get_user_by_login(
        login: str,
        user_repo: UserRepository = Depends(get_user_repository)
):
    user = await user_repo.get_user_by_login(login)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_uuid}", response_model=UserResponse)
async def update_user(
        user_uuid: UUID,
        user_update: UserUpdate,
        user_repo: UserRepository = Depends(get_user_repository)
):
    existing_user = await user_repo.get_user(user_uuid)
    if existing_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check unique constraints
    if user_update.login:
        existing_login = await user_repo.get_user_by_login(user_update.login)
        if existing_login and existing_login.uuid != user_uuid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Login already taken"
            )

    if user_update.email:
        existing_email = await user_repo.get_user_by_email(user_update.email)
        if existing_email and existing_email.uuid != user_uuid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )

    if user_update.telegram_login:
        existing_telegram = await user_repo.get_user_by_telegram(user_update.telegram_login)
        if existing_telegram and existing_telegram.uuid != user_uuid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telegram login already taken"
            )

    update_data = user_update.dict(exclude_unset=True)
    updated_user = await user_repo.update_user_partial(user_uuid, update_data)

    if updated_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return updated_user


@router.patch("/{user_uuid}/email", response_model=UserResponse)
async def update_user_email(
        user_uuid: UUID,
        email_update: UserEmailUpdate,
        user_repo: UserRepository = Depends(get_user_repository)
):
    existing_user = await user_repo.get_user(user_uuid)
    if existing_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check email uniqueness
    existing_email = await user_repo.get_user_by_email(email_update.email)
    if existing_email and existing_email.uuid != user_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already taken"
        )

    update_data = email_update.dict(exclude_unset=True)
    updated_user = await user_repo.update_user_partial(user_uuid, update_data)

    return updated_user


@router.patch("/{user_uuid}/telegram", response_model=UserResponse)
async def update_user_telegram(
        user_uuid: UUID,
        telegram_update: UserTelegramUpdate,
        user_repo: UserRepository = Depends(get_user_repository)
):
    existing_user = await user_repo.get_user(user_uuid)
    if existing_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check telegram uniqueness
    #existing_telegram = await user_repo.get_user_by_telegram(telegram_update.telegram_login)
    #if existing_telegram and existing_telegram.uuid != user_uuid:
    #    raise HTTPException(
    #        status_code=status.HTTP_400_BAD_REQUEST,
    #        detail="Telegram login already taken"
    #    )

    update_data = telegram_update.dict(exclude_unset=True)
    updated_user = await user_repo.update_user_partial(user_uuid, update_data)

    return updated_user


@router.delete("/{user_uuid}", status_code=status.HTTP_200_OK)
async def delete_user(
        user_uuid: UUID,
        user_repo: UserRepository = Depends(get_user_repository)
):
    success = await user_repo.delete_user(user_uuid)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "User deleted successfully"}