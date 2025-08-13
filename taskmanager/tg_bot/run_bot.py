import os
import sys
import django
# from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from django.utils.crypto import get_random_string
from asgiref.sync import sync_to_async

# Django init
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "taskmanager.settings")
# load_dotenv(os.path.join(BASE_DIR, ".env"))
django.setup()

# Импорт модели
from tasks.models import TelegramProfile

# URL фронтенда
FRONTEND_URL = "https://taskino-3hzc.onrender.com"

# Проверка привязки
@sync_to_async
def is_linked(chat_id):
    return TelegramProfile.objects.filter(chat_id=chat_id, user__isnull=False).exists()

# Генерация токена
@sync_to_async
def create_temp_token(chat_id):
    token = get_random_string(16)
    profile, _ = TelegramProfile.objects.get_or_create(chat_id=chat_id)
    profile.temp_token = token
    profile.save()
    return token

# Отвязка профиля
@sync_to_async
def unlink_profile(chat_id):
    TelegramProfile.objects.filter(chat_id=chat_id).update(user=None)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    linked = await is_linked(chat_id)

    await update.message.reply_text("👋 Вітаємо у Telegram-боті Taskino! ааааааа")

    if linked:
        keyboard = [[InlineKeyboardButton("❌ Відв'язати Telegram", callback_data="unlink")]]
    else:
        token = await create_temp_token(chat_id)
        link = f"{FRONTEND_URL}/telegram/confirm?token={token}&chat_id={chat_id}"
        keyboard = [[InlineKeyboardButton("🔗 Прив'язати Telegram", url=link)]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Оберіть дію:", reply_markup=reply_markup)

# Обработка кнопок (callback)
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "unlink":
        chat_id = query.message.chat.id
        await unlink_profile(chat_id)
        await query.edit_message_text("✅ Telegram успішно відв'язано.\n\nНадішліть /start для повторної прив'язки.")

# Запуск бота
def main():
    app = ApplicationBuilder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.run_polling()

if __name__ == "__main__":
    main()
