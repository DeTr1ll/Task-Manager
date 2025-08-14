from decouple import config

TELEGRAM_TOKEN = config("TELEGRAM_BOT_TOKEN")
BOT_PORT = int(config("BOT_PORT", 8443))
