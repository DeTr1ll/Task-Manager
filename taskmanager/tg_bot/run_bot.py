# tg_bot/run_bot.py
import os
import django
import sys
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from django.utils.crypto import get_random_string
from asgiref.sync import sync_to_async
from dotenv import load_dotenv

# Django init
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "taskmanager.settings")
load_dotenv(os.path.join(BASE_DIR, ".env"))
django.setup()

from tasks.models import TelegramProfile

FRONTEND_URL = "https://taskino-3hzc.onrender.com"

@sync_to_async
def create_temp_token(chat_id):
    token = get_random_string(16)
    profile, _ = TelegramProfile.objects.get_or_create(chat_id=chat_id)
    profile.temp_token = token
    profile.save()
    return token

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    token = await create_temp_token(chat_id)
    link = f"{FRONTEND_URL}/telegram/confirm?token={token}&chat_id={chat_id}"

    await update.message.reply_text(
        "🔗 Чтобы привязать Telegram к своему аккаунту на сайте, перейди по ссылке:\n\n"
        f"{link}\n\n"
        "Важно: ты должен быть авторизован на сайте в браузере."
    )

def main():
    app = ApplicationBuilder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
