import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from asgiref.sync import sync_to_async
from tasks.models import TelegramProfile
from .settings import FRONTEND_URL

# --- Асинхронные функции для работы с БД ---
@sync_to_async
def is_linked(chat_id: int) -> bool:
    return TelegramProfile.objects.filter(chat_id=chat_id, user__isnull=False).exists()

@sync_to_async
def create_temp_token(chat_id: int) -> str:
    from django.utils.crypto import get_random_string
    token = get_random_string(16)
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
