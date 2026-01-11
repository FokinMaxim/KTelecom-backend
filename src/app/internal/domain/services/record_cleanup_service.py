from sqlalchemy.orm import Session
from sqlalchemy import text
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime


@dataclass
class ExpiredRecordDTO:
    record_id: UUID
    user_id: UUID
    queue_id: UUID
    status: str
    meeting_datetime: datetime

class RecordCleanupService:
    def __init__(self, db: Session):
        self.db = db

    def get_expired_records(self) -> list[ExpiredRecordDTO]:
        sql = text("""
            SELECT
                r.record_id,
                r.user_id,
                r.queue_id,
                r.status,
                r.meeting_datetime
            FROM records r
            JOIN queues q ON r.queue_id = q.queue_id
            WHERE r.status IN ('PENDING', 'REJECTED')
              AND now() - r.status_updated_at > q.cleanup_interval
        """)

        rows = self.db.execute(sql).mappings().all()

        return [
            ExpiredRecordDTO(**row)
            for row in rows
        ]

    def delete_records(self, record_ids: list[str]) -> int:
        if not record_ids:
            return 0

        sql = text("""
            DELETE FROM records
            WHERE record_id = ANY(:ids)
        """)

        result = self.db.execute(sql, {"ids": record_ids})
        self.db.commit()

        return result.rowcount or 0