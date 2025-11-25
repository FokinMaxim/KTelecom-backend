from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from typing import List, Optional
from src.app.internal.data.models.user_model import UserModel
from src.app.internal.domain.entities.user_entity import UserEntity
from src.app.internal.domain.interfaces.user_interface import IUserRepository

class UserRepository(IUserRepository):
    def __init__(self, db: Session):
        self.db = db

    async def create_user(self, user: UserEntity) -> UserEntity:
        user_data = user.dict(exclude_none=True)

        if 'uuid' not in user_data or user_data['uuid'] is None:
            user_data['uuid'] = uuid4()

        db_user = UserModel(**user_data)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return UserEntity.from_orm(db_user)

    async def get_user(self, user_uuid: UUID) -> Optional[UserEntity]:
        db_user = self.db.query(UserModel).filter(UserModel.uuid == user_uuid).first()
        if db_user:
            return UserEntity.from_orm(db_user)
        return None

    async def get_user_by_email(self, email: str) -> Optional[UserEntity]:
        db_user = self.db.query(UserModel).filter(UserModel.email == email).first()
        if db_user:
            return UserEntity.from_orm(db_user)
        return None

    async def get_user_by_login(self, login: str) -> Optional[UserEntity]:
        db_user = self.db.query(UserModel).filter(UserModel.login == login).first()
        if db_user:
            return UserEntity.from_orm(db_user)
        return None

    async def get_all_users(self) -> List[UserEntity]:
        db_users = self.db.query(UserModel).all()
        return [UserEntity.from_orm(user) for user in db_users]

    async def update_user(self, user_uuid: UUID, user: UserEntity) -> Optional[UserEntity]:
        db_user = self.db.query(UserModel).filter(UserModel.uuid == user_uuid).first()
        if db_user:
            for key, value in user.dict().items():
                setattr(db_user, key, value)
            self.db.commit()
            self.db.refresh(db_user)
            return UserEntity.from_orm(db_user)
        return None

    async def update_user_partial(self, user_uuid: UUID, update_data: dict) -> Optional[UserEntity]:
        db_user = self.db.query(UserModel).filter(UserModel.uuid == user_uuid).first()
        if db_user:
            for key, value in update_data.items():
                if hasattr(db_user, key):
                    setattr(db_user, key, value)
            self.db.commit()
            self.db.refresh(db_user)
            return UserEntity.from_orm(db_user)
        return None

    async def delete_user(self, user_uuid: UUID) -> bool:
        db_user = self.db.query(UserModel).filter(UserModel.uuid == user_uuid).first()
        if db_user:
            self.db.delete(db_user)
            self.db.commit()
            return True
        return False
