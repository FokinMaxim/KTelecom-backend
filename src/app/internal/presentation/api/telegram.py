from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.app.internal.data.repositories.user_repository import UserRepository
from src.config.database import SessionLocal

router = Router()


@router.message(Command("start"))
async def start(message: Message):
    db = SessionLocal()          # ✅ реальная Session
    try:
        user_repo = UserRepository(db)

        if not message.from_user.username:
            await message.answer("У вас нет username в Telegram")
            return

        await user_repo.save_telegram_chat_id(
            username=message.from_user.username,
            chat_id=message.chat.id,
        )

        await message.answer("✅ Telegram успешно привязан")

    finally:
        db.close()