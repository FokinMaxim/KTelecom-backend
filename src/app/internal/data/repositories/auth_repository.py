# auth_repository.py
from datetime import datetime, timedelta

from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
import secrets
from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.app.internal.data.models.refresh_token_model import RefreshTokenModel
from src.app.internal.data.repositories.user_repository import UserRepository
from src.app.internal.domain.entities.user_entity import UserEntity
from src.app.internal.domain.services.auth_service import verify_password, get_password_hash, create_access_token, decode_access_token
from src.app.internal.presentation.scheme.user_schema import UserRegister


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthRepository:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    # Методы для работы с refresh токенами
    async def create_refresh_token(self, user_uuid: UUID, expires_days: int = 7) -> str:
        raw = secrets.token_urlsafe(32)
        hash_ = pwd_context.hash(raw)
        expires_at = datetime.utcnow() + timedelta(days=expires_days)
        rt = RefreshTokenModel(user_uuid=user_uuid, token_hash=hash_, expires_at=expires_at)
        self.db.add(rt)
        self.db.commit()
        self.db.refresh(rt)
        return raw

    async def find_valid_refresh_token(self, raw_token: str) -> Optional[RefreshTokenModel]:
        now = datetime.utcnow()
        candidates = self.db.query(RefreshTokenModel).filter(
            RefreshTokenModel.revoked == False,
            RefreshTokenModel.expires_at > now
        ).all()
        for c in candidates:
            try:
                if pwd_context.verify(raw_token, c.token_hash):
                    return c
            except Exception:
                continue
        return None

    async def revoke_refresh_token_by_model(self, rt: RefreshTokenModel):
        rt.revoked = True
        self.db.add(rt)
        self.db.commit()
        self.db.refresh(rt)
        return rt

    async def revoke_refresh_token_by_string(self, refresh_token: str):
        rt = await self.find_valid_refresh_token(refresh_token)
        if rt:
            await self.revoke_refresh_token_by_model(rt)

    async def revoke_user_tokens(self, user_uuid: UUID):
        self.db.query(RefreshTokenModel).filter(
            RefreshTokenModel.user_uuid == user_uuid,
            RefreshTokenModel.revoked == False
        ).update({RefreshTokenModel.revoked: True})
        self.db.commit()

    # Методы для работы с пользователями
    async def get_user_by_login(self, login: str):
        return await self.user_repo.get_user_by_login(login)

    async def get_user_by_uuid(self, user_uuid: UUID):
        return await self.user_repo.get_user(user_uuid)

    async def create_user(self, user_entity: UserEntity):
        return await self.user_repo.create_user(user_entity)

    async def authenticate_user(self, login: str, password: str):
        user = await self.get_user_by_login(login)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        access_token = create_access_token(subject=str(user.uuid))
        refresh_token = await self.create_refresh_token(user_uuid=user.uuid)

        return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}

    async def refresh_tokens(self, refresh_token: str):
        rt = await self.find_valid_refresh_token(refresh_token)
        if rt is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        if rt.revoked:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")

        await self.revoke_refresh_token_by_model(rt)

        user = await self.get_user_by_uuid(rt.user_uuid)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        access_token = create_access_token(subject=str(user.uuid))
        new_refresh_token = await self.create_refresh_token(user.uuid)

        return {"access_token": access_token, "token_type": "bearer", "refresh_token": new_refresh_token}

    async def get_user_from_token(self, token: str):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        payload = decode_access_token(token)
        if payload is None:
            raise credentials_exception

        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception

        try:
            user_uuid = UUID(str(sub))
        except Exception:
            raise credentials_exception

        user = await self.get_user_by_uuid(user_uuid)
        if user is None:
            raise credentials_exception

        return user

    async def register_user(self, user_in: UserRegister):
        try:
            hashed = get_password_hash(user_in.password)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Server error while hashing password")

        user_data = user_in.dict(exclude={"password"})
        user_data["password_hash"] = hashed

        if "uuid" in user_data:
            del user_data["uuid"]

        try:
            user_entity = UserEntity(**user_data)
        except TypeError as e:
            raise HTTPException(status_code=500, detail=f"UserEntity construction error: {e}")

        try:
            created = await self.create_user(user_entity)
        except IntegrityError as ie:
            if "login" in str(ie).lower():
                raise HTTPException(status_code=400, detail="User with this login already exists")
            elif "email" in str(ie).lower():
                raise HTTPException(status_code=400, detail="User with this email already exists")
            else:
                raise HTTPException(status_code=400, detail="User with given credentials already exists")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create user: {e}")

        return created
