from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from passlib.context import CryptContext
import secrets
from typing import Optional
from src.app.internal.data.models.refresh_token_model import RefreshTokenModel
from uuid import UUID

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_refresh_token(self, user_uuid: UUID, expires_days: int = 7) -> str:
        raw = secrets.token_urlsafe(32)
        hash_ = pwd_context.hash(raw)
        expires_at = datetime.utcnow() + timedelta(days=expires_days)
        rt = RefreshTokenModel(user_uuid=user_uuid, token_hash=hash_, expires_at=expires_at)
        self.db.add(rt)
        self.db.commit()
        self.db.refresh(rt)
        return raw

    def find_valid_refresh_token(self, raw_token: str) -> Optional[RefreshTokenModel]:
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

    def revoke_refresh_token(self, rt: RefreshTokenModel):
        rt.revoked = True
        self.db.add(rt)
        self.db.commit()
        self.db.refresh(rt)
        return rt

    def revoke_user_tokens(self, user_uuid: UUID):
        self.db.query(RefreshTokenModel).filter(
            RefreshTokenModel.user_uuid == user_uuid,
            RefreshTokenModel.revoked == False
        ).update({RefreshTokenModel.revoked: True})
        self.db.commit()
