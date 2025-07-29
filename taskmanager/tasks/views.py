from datetime import timedelta
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Case, When, Value, IntegerField
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, permissions
import hashlib
import hmac
from django.conf import settings
from django.contrib.auth import login
from django.http import HttpResponseBadRequest
from django.utils.http import urlencode
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from tasks.models import Task, TelegramProfile
from django.utils.timezone import now
from telegram import Bot
import os

import json

from .forms import TaskForm
from .models import Task, Tag, TelegramProfile
from .serializers import TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Аккаунт створено. Тепер увійдіть в нього.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'tasks/register.html', {'form': form})

@login_required
def task_list(request):
    tasks = Task.objects.filter(user=request.user)
    today = timezone.localdate()

    status_filter = request.GET.get('status')
    query = request.GET.get('q')

    if status_filter:
        tasks = tasks.filter(status=status_filter)

    if query:
        tasks = tasks.filter(
            Q(title__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()

    # Сортировка: сначала невыполненные, затем по дедлайну
    tasks = tasks.annotate(
        completed_order=Case(
            When(status='completed', then=Value(1)),
            default=Value(0),
            output_field=IntegerField()
        )
    ).order_by('completed_order', 'due_date', '-created_at')

    # Добавляем поле для подсветки даты
    task_list = list(tasks)
    for task in task_list:
        if task.status == 'completed':
            task.card_highlight = 'list-group-item-success'
            task.due_highlight = 'text-muted'
        elif task.due_date:
            if task.due_date < today:
                task.card_highlight = ''
                task.due_highlight = 'text-danger'
            elif task.due_date <= today + timedelta(days=0):
                task.card_highlight = ''
                task.due_highlight = 'text-warning'
            else:
                task.card_highlight = ''
                task.due_highlight = 'text-muted'
        else:
            task.card_highlight = ''
            task.due_highlight = 'text-muted'

    return render(request, 'tasks/tasks.html', {
        'tasks': task_list,
        'status_filter': status_filter,
        'query': query,
    })


@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user) 
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            tags = handle_tags_input(form.cleaned_data.get('tags_input', ''), request.user)
            task.save()
            task.tags.set(tags)
            form.save_m2m()
            messages.success(request, '<i class="bi bi-check2"></i> Задачу успішно створено.')
            return redirect('task_list')
    else:
        form = TaskForm(user=request.user)

    return render(request, 'tasks/task_form.html', {
        'form': form,
        'is_edit': False
    })

@login_required
def task_edit(request, id):
    task = get_object_or_404(Task, id=id, user=request.user)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()

            tags_input = form.cleaned_data.get('tags_input', '')
            tags = handle_tags_input(tags_input, request.user)
            task.tags.set(tags)

            messages.info(request, '<i class="bi bi-pencil-fill"></i> Задачу оновлено.')
            return redirect('task_list')
    else:
        form = TaskForm(instance=task, user=request.user)

    return render(request, 'tasks/task_form.html', {'form': form, 'is_edit': True})

@login_required
@require_POST
def task_update_status_ajax(request, id):
    task = get_object_or_404(Task, id=id, user=request.user)
    new_status = request.POST.get('status')

    valid_statuses = ['pending', 'in_progress', 'completed']
    if new_status not in valid_statuses:
        return JsonResponse({'success': False, 'error': 'Невірний статус'}, status=400)

    task.status = new_status
    task.save()
    return JsonResponse({'success': True, 'new_status_display': task.get_status_display()})

@require_POST
@login_required
def task_delete(request, id):
    task = get_object_or_404(Task, id=id, user=request.user)
    task.delete()
    messages.warning(request, '<i class="bi bi-trash-fill"></i> Задачу видалено.')
    return redirect('task_list')

def handle_tags_input(tags_str, user):
    tag_names = [t.strip() for t in tags_str.split(',') if t.strip()]
    tags = []
    for name in tag_names:
        tag, created = Tag.objects.get_or_create(name=name, user=user)
        tags.append(tag)
    return tags

@login_required
def tag_autocomplete(request):
    term = request.GET.get('term', '')
    user = request.user if request.user.is_authenticated else None
    tags = []

    if term and user:
        tags = Tag.objects.filter(name__icontains=term, user=user).values_list('name', flat=True).distinct()

    return JsonResponse(list(tags), safe=False)

@login_required
def confirm_telegram(request):
    token = request.GET.get("token")
    chat_id = request.GET.get("chat_id")
    if not request.user.is_authenticated:
        query = urlencode({'next': request.get_full_path()})
        return redirect(f'{settings.LOGIN_URL}?{query}')
    
    if not token or not chat_id:
        messages.error(request, "Неверная ссылка")
        return redirect("/")

    try:
        profile = TelegramProfile.objects.get(temp_token=token)
    except TelegramProfile.DoesNotExist:
        messages.error(request, "Токен не найден или устарел.")
        return redirect("/")

    profile.chat_id = chat_id
    profile.user = request.user
    profile.temp_token = None
    profile.save()

    if profile.chat_id:
            notify_telegram_on_link(profile.chat_id)

    messages.success(request, "✅ Telegram успешно привязан!")
    return redirect("/")

def notify_telegram_on_link(chat_id: int):
    token = settings.TELEGRAM_BOT_TOKEN
    message = "✅ Telegram успішно прив'язано! Тепер ви можете отримувати сповіщення."
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "❌ Відв'язати Telegram", "callback_data": "unlink"}]
        ]
    }

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "reply_markup": keyboard
    }
    
    requests.post(url, json=data)

@csrf_exempt
def trigger_deadlines(request):
    print("trigger_deadlines вызван")
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    auth_header = request.headers.get("Authorization")
    print(f"Authorization header: {auth_header}")

    if auth_header != f"Bearer {os.getenv('CRON_SECRET')}":
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    today = now().date()
    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    profiles = TelegramProfile.objects.exclude(chat_id=None).select_related("user")

    for profile in profiles:
        user = profile.user
        chat_id = profile.chat_id
        tasks_today = Task.objects.filter(user=user, deadline__date=today, completed=False)

        if not tasks_today.exists():
            continue

        message = "🗓️ *Сьогоднішні дедлайни:*\n\n"
        for task in tasks_today:
            message += f"• {task.title} — 🕓 {task.deadline.strftime('%H:%M')}\n"

        bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")

    return JsonResponse({'status': 'ok'})