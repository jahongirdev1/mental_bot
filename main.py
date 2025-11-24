import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.ai_handlers import router as ai_router
from bot.handlers import router as wellbeing_router
from config import settings


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    if not settings.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN орнатылмаған.")
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY орнатылмаған.")

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(wellbeing_router)
    dp.include_router(ai_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    print("Bot іске қосылуда...")
    asyncio.run(main())
