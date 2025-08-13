import subprocess
import os
import sys
import django

# Настройка Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "taskmanager.settings")
django.setup()

# Миграции и статика
subprocess.run(["python", "manage.py", "migrate"])
subprocess.run(["python", "manage.py", "collectstatic", "--noinput"])

# Запуск Gunicorn в фоне
gunicorn = subprocess.Popen([
    "gunicorn",
    "taskmanager.wsgi:application",
    "--bind", f"0.0.0.0:{os.environ.get('PORT', '8000')}"
])

# Импорт и запуск бота
from tg_bot.run_bot import main as bot_main

# Бот будет работать в foreground, Render видит процесс
bot_main()
