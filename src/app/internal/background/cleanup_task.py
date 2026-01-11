import asyncio
import logging

from fastapi import Depends
from src.app.internal.domain.services.notification_service import NotificationService
from src.app.internal.presentation.api.dependencies import get_notification_service
from src.config.database import SessionLocal
from src.app.internal.domain.services.record_cleanup_service import (
    RecordCleanupService
)
CLEANUP_INTERVAL_SECONDS = 60 * 60

logger = logging.getLogger(__name__)


async def cleanup_loop(notification_service: NotificationService = Depends(get_notification_service)):
    logger.info("Record cleanup loop started")

    while True:
        try:
            db = SessionLocal()
            try:
                cleanup_service = RecordCleanupService(db)
                records = cleanup_service.get_expired_records()

                for record in records:
                    if record.status == "pending":
                        await notification_service.notify_record_expired(record)

                deleted = cleanup_service.delete_records(
                    [r.record_id for r in records]
                )

                logger.info(f"Cleanup deleted {deleted} records")

            finally:
                db.close()

        except Exception:
            logger.exception("Error during record cleanup")

        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)