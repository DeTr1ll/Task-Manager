import os
import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from .handlers import start, button_callback
from .settings import TELEGRAM_TOKEN

# Создаём один Application
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Регистрируем хэндлеры
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_callback))

# Флаг готовности
_bot_ready = False

async def init_bot():
    """Инициализирует бота один раз."""
    global _bot_ready
    if not _bot_ready:
        await application.initialize()
        await application.start()
        _bot_ready = True

async def process_update_async(update):
    """Обработка апдейта (вебхук)."""
    await init_bot()
    await application.process_update(update)
