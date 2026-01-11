from pycparser.ply.yacc import Production

from src.app.internal.domain.entities.record_entity import RecordEntity
from src.app.internal.domain.interfaces.user_interface import IUserRepository
from src.app.internal.domain.services.record_cleanup_service import ExpiredRecordDTO
from src.app.internal.notifications.email_sender import EmailSender
from src.app.internal.notifications.telegram_sender import TelegramAiogramChannel



class NotificationService:
    def __init__(
            self,
            email_sender: EmailSender,
            user_repository: IUserRepository,
            telegram_channel: TelegramAiogramChannel = None,
    ):
        self.email_sender = email_sender
        self.user_repository = user_repository
        self.telegram_channel = telegram_channel

    async def _send_email(self, user, subject: str, text: str) -> bool:
        """Отправляет email и возвращает результат"""
        if not user.email_notifications or not user.email:
            return False

        try:
            await self.email_sender.send(
                recipient=user.email,
                subject=subject,
                text=text,
            )
            return True
        except Exception as e:
            print(f"✗ Failed to send email to {user.email}: {e}")
            return False

    async def _send_telegram(self, user, message: str) -> bool:
        """Отправляет Telegram и возвращает результат"""
        if (not self.telegram_channel or
                not user.telegram_notifications or
                not user.telegram_chat_id):
            print('Cannot send telegram message', user.telegram_chat_id, user.telegram_notifications)
            return False

        try:
            await self.telegram_channel.send(
                chat_id=user.telegram_chat_id,
                message=message
            )
            print(f"✓ Telegram sent to {user.telegram_login}")
            return True
        except Exception as e:
            print(f"✗ Failed to send Telegram to {user.telegram_login}: {e}")
            return False

    async def notify_record_status_changed(
            self,
            old_record: RecordEntity,
            new_record: RecordEntity,
    ) -> None:
        """
        Отправляет уведомления владельцу записи, если статус изменился
        """
        if old_record.status == new_record.status:
            return

        user = await self.user_repository.get_user(old_record.user_id)

        if not user:
            return

        # Подготовка сообщений
        email_subject = "Статус вашей заявки изменён"

        email_text = (
            "Здравствуйте!\n\n"
            "Статус вашей заявки был изменён.\n\n"
            f"ID заявки: #{old_record.record_id}\n"
            f"Старый статус: {old_record.status.value}\n"
            f"Новый статус: {new_record.status.value}\n"
            f"Дата встречи: {new_record.meeting_datetime}\n"
            f"Цель: {new_record.purpose}\n\n"
            "С уважением,\n"
            "Система управления очередями"
        )

        telegram_message = (
            f"<b>🔄 Изменение статуса заявки</b>\n\n"
            f"<b>ID:</b> <code>#{old_record.record_id}</code>\n"
            f"<b>Статус:</b> {old_record.status.value} → <b>{new_record.status.value}</b>\n"
            f"<b>Дата:</b> {new_record.meeting_datetime}\n"
            f"<b>Цель:</b> {new_record.purpose}\n\n"
            f"<i>Для управления уведомлениями посетите ваш профиль в системе.</i>"
        )

        print(f"📤 Sending notifications for record #{old_record.record_id}...")

        # Отправляем параллельно
        email_sent = await self._send_email(user, email_subject, email_text)
        telegram_sent = await self._send_telegram(user, telegram_message)

        if email_sent or telegram_sent:
            print(f"✅ Notifications sent for record #{old_record.record_id}")
        else:
            print(f"⚠️ No notifications sent (all disabled or failed)")


    async def notify_queue_owner_record_created(
            self,
            record: RecordEntity,
            queue_owner_id,
    ) -> None:
        """
        Уведомляет владельца очереди о создании новой записи
        """
        user = await self.user_repository.get_user(queue_owner_id)

        if not user:
            print(f"⚠️ Queue owner {queue_owner_id} not found")
            return

        email_subject = "Новая запись в вашу очередь"

        email_text = (
            "Здравствуйте!\n\n"
            "В вашей очереди была создана новая запись.\n\n"
            f"ID записи: #{record.record_id}\n"
            f"Дата встречи: {record.meeting_datetime}\n"
            f"Цель: {record.purpose}\n"
            f"Статус: {record.status.value}\n\n"
            "С уважением,\n"
            "Система управления очередями"
        )

        telegram_message = (
            f"<b>📥 Новая запись в очереди</b>\n\n"
            f"<b>ID:</b> <code>#{record.record_id}</code>\n"
            f"<b>Дата:</b> {record.meeting_datetime}\n"
            f"<b>Цель:</b> {record.purpose}\n"
            f"<b>Статус:</b> <b>{record.status.value}</b>\n\n"
            f"<i>Перейдите в систему, чтобы управлять записью.</i>"
        )

        print(f"📤 Sending queue owner notifications for record #{record.record_id}...")

        email_sent = await self._send_email(user, email_subject, email_text)
        telegram_sent = await self._send_telegram(user, telegram_message)

        if email_sent or telegram_sent:
            print(f"✅ Queue owner notified about record #{record.record_id}")
        else:
            print(f"⚠️ Queue owner notifications not sent")


    async def notify_record_expired(self, record: ExpiredRecordDTO):
        user = await self.user_repository.get_user(record.user_id)

        if not user:
            return

        email_subject = "Заявка была удалена из очереди"

        email_text = (
            "Здравствуйте!\n\n"
            "Ваша заявка была автоматически удалена, так как долгое время "
            "находилась в статусе «Ожидает подтверждения».\n\n"
            f"ID заявки: #{record.record_id}\n"
            f"Дата встречи: {record.meeting_datetime}\n\n"
            "При необходимости вы можете создать новую заявку.\n\n"
            "С уважением,\n"
            "Система управления очередями"
        )

        telegram_message = (
            f"<b>❌ Заявка удалена</b>\n\n"
            f"<b>ID:</b> <code>#{record.record_id}</code>\n"
            f"<b>Причина:</b> ожидание подтверждения истекло\n\n"
            f"<i>Вы можете создать новую заявку в системе.</i>"
        )

        await self._send_email(user, email_subject, email_text)
        await self._send_telegram(user, telegram_message)


    async def close(self):
        """Закрывает ресурсы"""
        if self.telegram_channel:
            await self.telegram_channel.close()


    async def notify_record_rescheduled(
            self,
            old_record: RecordEntity,
            new_record: RecordEntity,
    ) -> None:
        """
        Уведомляет владельца записи о переносе времени встречи
        """
        user = await self.user_repository.get_user(old_record.user_id)
        print(user)

        if not user:
            print(f"⚠️ User {old_record.user_id} not found")
            return

        email_subject = "Время встречи было изменено"

        email_text = (
            "Здравствуйте!\n\n"
            "Владелец очереди изменил время вашей встречи.\n\n"
            f"ID заявки: #{old_record.record_id}\n"
            f"Старое время: {old_record.meeting_datetime}\n"
            f"Новое время: {new_record.meeting_datetime}\n"
            f"Цель: {new_record.purpose}\n\n"
            "Пожалуйста, убедитесь, что новое время вам подходит.\n\n"
            "С уважением,\n"
            "Система управления очередями"
        )

        telegram_message = (
            f"<b>⏰ Перенос встречи</b>\n\n"
            f"<b>ID:</b> <code>#{old_record.record_id}</code>\n"
            f"<b>Было:</b> {old_record.meeting_datetime}\n"
            f"<b>Стало:</b> <b>{new_record.meeting_datetime}</b>\n\n"
            f"<i>Изменение выполнено владельцем очереди.</i>"
        )

        await self._send_email(user, email_subject, email_text)
        await self._send_telegram(user, telegram_message)

    async def notify_record_owner_comment_added(
            self,
            record_id,
            record_owner_id,
            comment_text: str,
    ):
        """
        Уведомляет владельца записи о новом комментарии владельца очереди
        """
        user = await self.user_repository.get_user(record_owner_id)

        print(user)
        if not user:
            print(f"⚠️ Record owner {record_owner_id} not found")
            return

        email_subject = "Новый комментарий к вашей заявке"

        email_text = (
            "Здравствуйте!\n\n"
            "Владелец очереди добавил комментарий к вашей заявке.\n\n"
            f"ID заявки: #{record_id}\n\n"
            "Комментарий:\n"
            f"\"{comment_text}\"\n\n"
            "Пожалуйста, ознакомьтесь.\n\n"
            "С уважением,\n"
            "Система управления очередями"
        )

        telegram_message = (
            f"<b>💬 Новый комментарий</b>\n\n"
            f"<b>ID заявки:</b> <code>#{record_id}</code>\n\n"
            f"<b>Комментарий:</b>\n"
            f"{comment_text}"
        )

        await self._send_email(user, email_subject, email_text)
        await self._send_telegram(user, telegram_message)