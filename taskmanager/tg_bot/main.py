import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update, Bot
from tg_bot.settings import TELEGRAM_TOKEN
from tg_bot.handlers import start, button_callback
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
import asyncio

# создаём бота отдельно
bot = Bot(token=TELEGRAM_TOKEN)

# создаём приложение
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_callback))

@csrf_exempt
def telegram_webhook(request, token):
    if token != TELEGRAM_TOKEN:
        return JsonResponse({"ok": False, "error": "Invalid token"}, status=403)

    data = json.loads(request.body)
    update = Update.de_json(data, bot)  # <-- используем отдельно созданный Bot

    # Запускаем coroutine через asyncio.run
    asyncio.run(application.process_update(update))

    return JsonResponse({"ok": True})
