from decouple import config

TELEGRAM_TOKEN = config("TELEGRAM_BOT_TOKEN")
FRONTEND_URL = "https://taskino-3hzc.onrender.com"
BOT_PORT = int(config("BOT_PORT", 8443))