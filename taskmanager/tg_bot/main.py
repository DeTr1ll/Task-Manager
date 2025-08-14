from decouple import config
import requests

TOKEN = config("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set")

WEBHOOK_URL = f"https://{config('RENDER_EXTERNAL_HOSTNAME')}/bot/{TOKEN}/"

print("Setting webhook to", WEBHOOK_URL)
r = requests.post(f"https://api.telegram.org/bot{TOKEN}/setWebhook", json={"url": WEBHOOK_URL, "allowed_updates": ["message", "callback_query"]}, timeout=15)
print(r.status_code, r.text)
r.raise_for_status()
print("Webhook set")
