import os
import django
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from django.utils.crypto import get_random_string
from asgiref.sync import sync_to_async

# --- Django setup ---
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
import sys
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "taskmanager.settings")
django.setup()

# --- Модели ---
from tasks.models import TelegramProfile

# --- Настройки ---
FRONTEND_URL = "https://taskino-3hzc.onrender.com"
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# --- Асинхронные функции для работы с БД ---
@sync_to_async
def is_linked(chat_id):
    return TelegramProfile.objects.filter(chat_id=chat_id, user__isnull=False).exists()

@sync_to_async
def create_temp_token(chat_id):
    token = get_random_string(16)
    profile, _ = TelegramProfile.objects.get_or_create(chat_id=chat_id)
    profile.temp_token = token
    profile.save()
    return token

@sync_to_async
def unlink_profile(chat_id):
    TelegramProfile.objects.filter(chat_id=chat_id).update(user=None)

# --- Хэндлеры ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    linked = await is_linked(chat_id)

    await update.message.reply_text("👋 Вітаємо у Telegram-боті Taskino!")

    if linked:
        keyboard = [[InlineKeyboardButton("❌ Відв'язати Telegram", callback_data="unlink")]]
    else:
        token = await create_temp_token(chat_id)
        link = f"{FRONTEND_URL}/telegram/confirm?token={token}&chat_id={chat_id}"
        keyboard = [[InlineKeyboardButton("🔗 Прив'язати Telegram", url=link)]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Оберіть дію:", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "unlink":
        chat_id = query.message.chat.id
        await unlink_profile(chat_id)
        await query.edit_message_text("✅ Telegram успішно відв'язано.\n\nНадішліть /start для повторної прив'язки.")

# --- Запуск бота ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))

    # Webhook
    port = int(os.environ.get("BOT_PORT", 8443))
    webhook_path = BOT_TOKEN
    webhook_url = f"{FRONTEND_URL}/webhook/{BOT_TOKEN}/"

    print(f"Запуск Webhook на {webhook_url}")
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=webhook_path,
        webhook_url=webhook_url,
    )

if __name__ == "__main__":
    main()
