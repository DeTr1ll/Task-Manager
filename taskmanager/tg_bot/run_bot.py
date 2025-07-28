import os
import sys
from dotenv import load_dotenv
import django
from decouple import config

# Добавляем корень проекта в sys.path, чтобы Python видел taskmanager.settings
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Загружаем переменные окружения из .env
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Устанавливаем настройки Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "taskmanager.settings")
django.setup()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from tasks.models import TelegramProfile, User
from django.utils.crypto import get_random_string

# Получаем токен из переменных окружения
TOKEN = config('TELEGRAM_BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔐 Логін", callback_data="login")],
    ]
    await update.message.reply_text(
        "Привіт! Цей бот надсилає нагадування про задачі з сайту.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "login":
        token = get_random_string(16)
        await query.edit_message_text(
            f"Перейди на сайт для прив’язки Telegram: https://taskino-3hzc.onrender.com/telegram/bind/{token}"
        )

application = ApplicationBuilder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_handler))

if __name__ == "__main__":
    application.run_polling()
