from sqlalchemy.exc import IntegrityError
from uuid import UUID

import os
from jose import JWTError, jwt

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.app.internal.domain.entities.user_entity import UserEntity
from src.app.internal.domain.services.auth_service import pwd_context
from src.config.database import get_db
from src.app.internal.presentation.scheme.auth_schema import TokenResponse, RefreshIn, LoginIn
from src.app.internal.data.repositories.user_repository import UserRepository
from src.app.internal.presentation.scheme.user_schema import UserResponse, UserCreate, UserRegister
from src.app.internal.data.repositories.auth_repository import AuthRepository
from src.app.internal.domain.services import auth_service


SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-prod")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


@router.post("/token", response_model=TokenResponse)
async def token(login_in: LoginIn, db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_login(login_in.login)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not auth_service.verify_password(login_in.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = auth_service.create_access_token(subject=str(user.uuid))

    auth_repo = AuthRepository(db)

    refresh_token = auth_repo.create_refresh_token(user_uuid=user.uuid)

    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshIn, db: Session = Depends(get_db)):
    auth_repo = AuthRepository(db)
    rt = auth_repo.find_valid_refresh_token(data.refresh_token)
    if rt is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if rt.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")

    auth_repo.revoke_refresh_token(rt)
    user_uuid = rt.user_uuid
    from src.app.internal.data.models.user_model import UserModel
    sa_user = db.query(UserModel).filter(UserModel.uuid == user_uuid).first()
    if sa_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    access_token = auth_service.create_access_token(subject=str(sa_user.uuid))
    refresh_token = auth_repo.create_refresh_token(sa_user)
    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}

@router.post("/logout")
async def logout(data: RefreshIn, db: Session = Depends(get_db)):
    auth_repo = AuthRepository(db)
    rt = auth_repo.find_valid_refresh_token(data.refresh_token)
    if rt:
        auth_repo.revoke_refresh_token(rt)
    return {"msg": "ok"}



async def get_current_user(token: str = Depends(oauth2_scheme),
                           user_repo: UserRepository = Depends(get_user_repo)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise credentials_exception

    sub = payload.get("sub")
    if sub is None:
        raise credentials_exception

    try:
        user_uuid = UUID(str(sub))
    except Exception:
        raise credentials_exception

    user = await user_repo.get_user(user_uuid)
    if user is None:
        raise credentials_exception

    return user


@router.get("/me", response_model=UserResponse)
async def read_own_profile(current_user = Depends(get_current_user)):
    """
    Возвращает данные текущего аутентифицированного пользователя.
    Пример заголовка запроса:
      Authorization: Bearer <access_token>
    """
    return current_user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
        user_in: UserRegister,
        user_repo: UserRepository = Depends(get_user_repo), ):
    try:
        hashed = pwd_context.hash(user_in.password)
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
        created = await user_repo.create_user(user_entity)
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