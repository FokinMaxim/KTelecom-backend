from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from typing import List, Optional

from src.app.internal.data.models.record_model import RecordModel
from src.app.internal.domain.entities.record_entity import RecordEntity
from src.app.internal.domain.interfaces.record_interface import IRecordRepository
from sqlalchemy.orm import selectinload
from src.app.internal.data.models.attachment_model import AttachmentModel


class RecordRepository(IRecordRepository):
    def __init__(self, db: Session):
        self.db = db

    async def create_record(self, record: RecordEntity) -> RecordEntity:
        record_data = record.dict(exclude_none=True)

        if "record_id" not in record_data or record_data["record_id"] is None:
            record_data["record_id"] = uuid4()

        db_record = RecordModel(**record_data)
        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)

        return RecordEntity.from_orm(db_record)

    async def get_record(self, record_id: UUID) -> Optional[RecordEntity]:
        db_record = (
            self.db.query(RecordModel)
            .options(selectinload(RecordModel.attachments))
            .filter(RecordModel.record_id == record_id)
            .first()
        )
        return RecordEntity.from_orm(db_record) if db_record else None

    async def get_records_by_queue(self, queue_id: UUID) -> List[RecordEntity]:
        records = (
            self.db.query(RecordModel)
            .options(selectinload(RecordModel.attachments))
            .filter(RecordModel.queue_id == queue_id)
            .all()
        )
        return [RecordEntity.from_orm(r) for r in records]

    async def get_records_by_user(self, user_id: UUID) -> List[RecordEntity]:
        records = (
            self.db.query(RecordModel)
            .options(selectinload(RecordModel.attachments))
            .filter(RecordModel.user_id == user_id)
            .all()
        )
        return [RecordEntity.from_orm(r) for r in records]

    async def update_record_partial(
        self,
        record_id: UUID,
        update_data: dict
    ) -> Optional[RecordEntity]:
        db_record = (
            self.db.query(RecordModel)
            .filter(RecordModel.record_id == record_id)
            .first()
        )

        if not db_record:
            return None

        for key, value in update_data.items():
            if hasattr(db_record, key) and key != "record_id":
                setattr(db_record, key, value)

        self.db.commit()
        self.db.refresh(db_record)
        return RecordEntity.from_orm(db_record)

    async def delete_record(self, record_id: UUID) -> bool:
        db_record = (
            self.db.query(RecordModel)
            .filter(RecordModel.record_id == record_id)
            .first()
        )

        if not db_record:
            return False

        self.db.delete(db_record)
        self.db.commit()
        return True

    async def has_time_collision(
            self,
            queue_id: UUID,
            meeting_datetime,
            interval
    ) -> bool:
        start = meeting_datetime - interval
        end = meeting_datetime + interval

        collision = (
            self.db.query(RecordModel)
            .filter(
                RecordModel.queue_id == queue_id,
                RecordModel.meeting_datetime > start,
                RecordModel.meeting_datetime < end,
            )
            .first()
        )

        return collision is not None
