import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.handlers import router
from config import settings


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=settings.BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
