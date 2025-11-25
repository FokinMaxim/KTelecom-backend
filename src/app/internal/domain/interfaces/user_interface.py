from abc import ABC, abstractmethod
from uuid import UUID
from typing import List, Optional
from src.app.internal.domain.entities.user_entity import UserEntity

class IUserRepository(ABC):

    @abstractmethod
    async def create_user(self, user: UserEntity) -> UserEntity:
        pass

    @abstractmethod
    async def get_user(self, user_uuid: UUID) -> Optional[UserEntity]:
        pass

    @abstractmethod
    async def get_user_by_login(self, login: str) -> Optional[UserEntity]:
        pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[UserEntity]:
        pass


    @abstractmethod
    async def get_all_users(self) -> List[UserEntity]:
        pass

    @abstractmethod
    async def update_user(self, user_uuid: UUID, user: UserEntity) -> Optional[UserEntity]:
        pass

    @abstractmethod
    async def delete_user(self, user_uuid: UUID) -> bool:
        pass

    @abstractmethod
    async def update_user_partial(self, user_uuid: UUID, update_data: dict) -> Optional[UserEntity]:
        pass
