from django.core.management.base import BaseCommand
from django.utils.timezone import now, timedelta
from django.conf import settings
from telegram import Bot
from asgiref.sync import async_to_sync
from tasks.models import Task, TelegramProfile

class Command(BaseCommand):
    help = "Надсилає нагадування в Telegram про дедлайни задач"

    def handle(self, *args, **kwargs):
        today = now().date()
        tomorrow = today + timedelta(days=1)

        profiles = TelegramProfile.objects.select_related('user')

        for profile in profiles:
            user = profile.user

            tasks = Task.objects.filter(
                user=user,
                status__in=['pending', 'in_progress'],
                due_date__range=[today, tomorrow]
            ).order_by("due_date")

            if not tasks.exists():
                continue

            message = f"🔔 *Нагадування про дедлайни*:\n"
            for task in tasks:
                message += f"• {task.title} — до {task.due_date.strftime('%d.%m')}\n"

            try:
                self.send_telegram_message(profile.chat_id, message)
                self.stdout.write(f"✅ Надіслано користувачу {user.username}")
            except Exception as e:
                self.stderr.write(f"⚠️ Помилка надсилання {user.username}: {e}")

    def send_telegram_message(self, chat_id, text):
        async def _send():
            bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")

        async_to_sync(_send)()
