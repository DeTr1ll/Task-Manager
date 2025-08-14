from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from asgiref.sync import sync_to_async
from tasks.models import TelegramProfile
from .settings import FRONTEND_URL, TELEGRAM_TOKEN
from django.utils.crypto import get_random_string
import asyncio

# --- Асинхронные функции для работы с БД ---
@sync_to_async
def is_linked(chat_id: int) -> bool:
    return TelegramProfile.objects.filter(chat_id=chat_id, user__isnull=False).exists()

@sync_to_async
def create_temp_token(chat_id: int) -> str:
    token = get_random_string(32)
    profile, _ = TelegramProfile.objects.get_or_create(chat_id=chat_id)
    profile.temp_token = token
    profile.save()
    return token

@sync_to_async
def unlink_profile(chat_id: int):
    TelegramProfile.objects.filter(chat_id=chat_id).update(user=None)

# --- Хэндлеры ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    linked = await is_linked(chat_id)

    if linked:
        button1 = KeyboardButton("Отвязать")
    else:
        button1 = KeyboardButton("Привязать")

    button2 = KeyboardButton("Сменить язык")
    keyboard = ReplyKeyboardMarkup([[button1, button2]], resize_keyboard=True)

    await update.message.reply_text("👋 Вітаємо у Telegram-боті Taskino!")
    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=keyboard
    )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    if text == "Привязать":
        token = await create_temp_token(chat_id)
        link = f"{FRONTEND_URL}/telegram/confirm?token={token}&chat_id={chat_id}"
        await update.message.reply_text(
            f"Нажмите для привязки: {link}"
        )

    elif text == "Отвязать":
        await unlink_profile(chat_id)
        await update.message.reply_text("✅ Аккаунт отвязан. Введите /start для обновления кнопок.")

    elif text == "Сменить язык":
        await update.message.reply_text("Выберите язык: 🇷🇺 Русский, 🇺🇸 English, ...")

