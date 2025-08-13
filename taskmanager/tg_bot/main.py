from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from tg_bot.settings import TELEGRAM_TOKEN
from tg_bot.handlers import start, button_callback  # ваши хэндлеры

# создаём приложение
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
# добавляем хэндлеры
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_callback))

@csrf_exempt
def telegram_webhook(request, token):
    if request.method == "POST":
        if token != TELEGRAM_TOKEN:
            return JsonResponse({"ok": False, "error": "invalid token"}, status=403)

        data = json.loads(request.body)

        # создаем Update с ботом
        update = Update.de_json(data, application.bot)

        # запускаем обработку обновления
        application.process_update(update)

        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False})
