import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from .settings import TELEGRAM_TOKEN, BOT_PORT
from . import handlers

# Создаем приложение бота
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Регистрируем хэндлеры
application.add_handler(CommandHandler("start", handlers.start))
application.add_handler(CallbackQueryHandler(handlers.button_callback))

# Функция для обработки update из Django webhook
async def process_update_async(update: Update):
    await application.process_update(update)

def process_update(update: Update):
    asyncio.run(process_update_async(update))
