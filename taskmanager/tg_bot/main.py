from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from .settings import TELEGRAM_TOKEN
from .handlers import start, button_callback

# Создаем приложение
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# Добавляем хэндлеры
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_callback))
