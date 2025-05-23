import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from bot.config import BOT_TOKEN
from bot.handlers import start

async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    
    # Добавляем хранилище для FSM
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    dp.include_router(start.router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)