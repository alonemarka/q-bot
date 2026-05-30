import asyncio
import logging
from aiogram import Bot, Dispatcher
from bot.config import BOT_TOKEN
from bot.handlers import router
from bot.database import init_db

async def main():
    await init_db()
    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher()
    dp.include_router(router)
    
    print("🚀 QuotLy Bot + Admin Panel Başladı!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
