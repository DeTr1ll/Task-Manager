import os
import asyncio
from telegram.ext import Application
from .handlers import register_handlers

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]

application = Application.builder().token(TELEGRAM_TOKEN).build()
register_handlers(application)

_bot_ready = False

async def init_bot():
    global _bot_ready
    if not _bot_ready:
        await application.initialize()
        await application.start()
        _bot_ready = True

async def process_update_async(update):
    await init_bot()
    await application.process_update(update)
