from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.app.internal.presentation.scheme.auth_schema import TokenResponse, RefreshIn, LoginIn
from src.app.internal.presentation.scheme.user_schema import UserResponse, UserRegister

from src.app.internal.data.repositories.auth_repository import AuthRepository


router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_auth_repository(db: Session = Depends(get_db)):
    return AuthRepository(db)


@router.post("/token", response_model=TokenResponse)
async def token(
    login_in: LoginIn,
    auth_repo: AuthRepository = Depends(get_auth_repository)
):
    try:
        tokens = await auth_repo.authenticate_user(login_in.login, login_in.password)
        return tokens
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshIn,
    auth_repo: AuthRepository = Depends(get_auth_repository)
):
    try:
        tokens = await auth_repo.refresh_tokens(data.refresh_token)
        return tokens
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/logout")
async def logout(
    data: RefreshIn,
    auth_repo: AuthRepository = Depends(get_auth_repository)
):
    try:
        await auth_repo.revoke_refresh_token_by_string(data.refresh_token)
        return {"msg": "ok"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_repo: AuthRepository = Depends(get_auth_repository)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    user = await auth_repo.get_user_from_token(token)
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
    auth_repo: AuthRepository = Depends(get_auth_repository)
):
    try:
        user = await auth_repo.register_user(user_in)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))