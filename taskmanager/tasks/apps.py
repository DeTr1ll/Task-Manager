from django.apps import AppConfig
import asyncio
import threading


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks'

    def ready(self):
            from tg_bot.async_bot import main as bot_main

            # Запуск бота в отдельном потоке
            def run_bot():
                asyncio.run(bot_main())

            threading.Thread(target=run_bot, daemon=True).start()
