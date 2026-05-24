import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.handlers import goal, instruction, photo, start
from config.settings import get_settings
from database.session import create_db


async def main() -> None:
    settings = get_settings()
    bot_token = settings.effective_telegram_bot_token
    if not bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required to run the bot")

    logging.basicConfig(level=logging.INFO)
    create_db()
    bot = Bot(token=bot_token)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start.router)
    dp.include_router(instruction.router)
    dp.include_router(photo.router)
    dp.include_router(goal.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
