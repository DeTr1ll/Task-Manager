# bot.py

import os
import django

# Инициализация Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "taskmanager.settings")  # замените на свое имя проекта
django.setup()

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
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
    keyboard = [
        [InlineKeyboardButton("🔐 Увійти через Telegram", url="https://t.me/your_bot_username?start=connect")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Цей бот надсилає вам нагадування про дедлайни задач з сайту.\n"
        "Щоб почати отримувати повідомлення, увійдіть у свій акаунт:",
        reply_markup=reply_markup
    )

# Запит логина
async def ask_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    user = await sync_to_async(authenticate)(username=login, password=password)

    if user:
        chat_id = update.message.chat_id

        await sync_to_async(TelegramProfile.objects.update_or_create)(
            user=user,
            defaults={"chat_id": chat_id}
        )

        keyboard = [[KeyboardButton("❌ Відмовитися від розсилки")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(
            f"✅ Успішно прив'язано до акаунту *{user.username}*!",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("❌ Невірні логін або пароль. Спробуйте ще раз командою /start")
    return ConversationHandler.END

# Команда отмены
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Авторизацію скасовано.")
    return ConversationHandler.END

# Команда для відмови від розсилки
async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    try:
        profile = await sync_to_async(TelegramProfile.objects.get)(chat_id=chat_id)
        profile.chat_id = None
        await sync_to_async(profile.save)()

        keyboard = [[KeyboardButton("🔐 Увійти")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(
            "🔕 Ви успішно відмовились від розсилки.",
            reply_markup=reply_markup
        )
    except TelegramProfile.DoesNotExist:
        await update.message.reply_text("Ви ще не підключали Telegram до акаунту.")

def main():
    application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔐 Увійти$"), ask_login)],
        states={
            LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_login)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.Regex("^❌ Відмовитися від розсилки$"), unsubscribe))

    print("🤖 Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
