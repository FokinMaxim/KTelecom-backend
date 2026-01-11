from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from src.app.internal.domain.services.notification_channel import NotificationChannel


class TelegramAiogramChannel(NotificationChannel):
    def __init__(self, bot_token: str):
        self.bot = Bot(
            token=bot_token,
            default=DefaultBotProperties(parse_mode="HTML"),
        )

    async def send(self, chat_id: int, message: str) -> None:
        """
        Отправляет сообщение пользователю Telegram через @username
        """
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message
            )

            print(f"Telegram notification sent to {chat_id}")

        except TelegramForbiddenError as e:
            # Пользователь заблокировал бота или не запускал его
            print(f"User {chat_id} has blocked the bot or not started it: {e}")
            raise

        except TelegramBadRequest as e:
            # Неправильный username или другие ошибки запроса
            print(f"Failed to send to {chat_id}: {e}")
            raise

        except Exception as e:
            print(f"Unexpected error sending to {chat_id}: {e}")
            raise

    async def close(self):
        """Закрывает сессию бота"""
        await self.bot.session.close()