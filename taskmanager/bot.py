# bot.py

import os
import django

# Инициализация Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "taskmanager.settings")  # замените на свое имя проекта
django.setup()

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
from django.conf import settings
from django.contrib.auth import authenticate
from tasks.models import TelegramProfile
from asgiref.sync import sync_to_async

# Этапы диалога
LOGIN, PASSWORD = range(2)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введіть ваш логін:")
    return LOGIN

# Прием логина
async def get_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["login"] = update.message.text
    await update.message.reply_text("Тепер введіть пароль:")
    return PASSWORD

# Обертка для безопасного доступа к базе
@sync_to_async
def authenticate_user_and_bind(login, password, chat_id):
    user = authenticate(username=login, password=password)
    if user:
        TelegramProfile.objects.update_or_create(
            user=user,
            defaults={"chat_id": chat_id},
        )
    return user

# Прием пароля и проверка
async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    login = context.user_data.get("login")
    password = update.message.text
    chat_id = update.message.chat_id

    user = await authenticate_user_and_bind(login, password, chat_id)

    if user:
        await update.message.reply_text(f"✅ Успішно прив'язано до акаунту {user.username}!")
    else:
        await update.message.reply_text("❌ Невірні логін або пароль. Спробуйте знову командою /start")

    return ConversationHandler.END

# Команда отмены
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Авторизацію скасовано.")
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_login)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    print("🤖 Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
