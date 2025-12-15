from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from typing import List, Optional
from src.app.internal.data.models.queue_model import QueueModel
from src.app.internal.domain.entities.queue_entity import QueueEntity
from src.app.internal.domain.interfaces.queue_interface import IQueueRepository

class QueueRepository(IQueueRepository):
    def __init__(self, db: Session):
        self.db = db

    async def create_queue(self, queue: QueueEntity) -> QueueEntity:
        queue_data = queue.dict(exclude_none=True)

        if 'queue_id' not in queue_data or queue_data['queue_id'] is None:
            queue_data['queue_id'] = uuid4()

        db_queue = QueueModel(**queue_data)
        self.db.add(db_queue)
        self.db.commit()
        self.db.refresh(db_queue)
        return QueueEntity.from_orm(db_queue)

    async def get_queue(self, queue_id: UUID) -> Optional[QueueEntity]:
        db_queue = self.db.query(QueueModel).filter(QueueModel.queue_id == queue_id).first()
        if db_queue:
            return QueueEntity.from_orm(db_queue)
        return None

    async def get_queue_by_name(self, name: str) -> Optional[QueueEntity]:
        db_queue = self.db.query(QueueModel).filter(QueueModel.name == name).first()
        if db_queue:
            return QueueEntity.from_orm(db_queue)
        return None

    async def get_queues_by_owner(self, owner_id: UUID) -> List[QueueEntity]:
        db_queues = self.db.query(QueueModel).filter(QueueModel.owner_id == owner_id).all()
        return [QueueEntity.from_orm(queue) for queue in db_queues]

    async def get_all_queues(self) -> List[QueueEntity]:
        db_queues = self.db.query(QueueModel).all()
        return [QueueEntity.from_orm(queue) for queue in db_queues]

    async def update_queue(self, queue_id: UUID, queue: QueueEntity) -> Optional[QueueEntity]:
        db_queue = self.db.query(QueueModel).filter(QueueModel.queue_id == queue_id).first()
        if db_queue:
            for key, value in queue.dict().items():
                if hasattr(db_queue, key) and key != 'queue_id':  # Не обновляем первичный ключ
                    setattr(db_queue, key, value)
            self.db.commit()
            self.db.refresh(db_queue)
            return QueueEntity.from_orm(db_queue)
        return None

    async def update_queue_partial(self, queue_id: UUID, update_data: dict) -> Optional[QueueEntity]:
        db_queue = self.db.query(QueueModel).filter(QueueModel.queue_id == queue_id).first()
        if db_queue:
            for key, value in update_data.items():
                if hasattr(db_queue, key) and key != 'queue_id':  # Не обновляем первичный ключ
                    setattr(db_queue, key, value)
            self.db.commit()
            self.db.refresh(db_queue)
            return QueueEntity.from_orm(db_queue)
        return None

    async def delete_queue(self, queue_id: UUID) -> bool:
        db_queue = self.db.query(QueueModel).filter(QueueModel.queue_id == queue_id).first()
        if db_queue:
            self.db.delete(db_queue)
            self.db.commit()
            return True
        return False