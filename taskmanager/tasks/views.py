from datetime import timedelta
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Case, When, Value, IntegerField
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from rest_framework import viewsets, permissions
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse, HttpResponseForbidden
import json
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.crypto import get_random_string

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
            messages.success(request, _('Account created. Please log in now.'))
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

    tasks = tasks.annotate(
        completed_order=Case(
            When(status='completed', then=Value(1)),
            default=Value(0),
            output_field=IntegerField()
        )
    ).order_by('completed_order', 'due_date', '-created_at')

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
            messages.success(request, '<i class="bi bi-check2"></i> ' + _('Task successfully created.'))
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

            messages.info(request, '<i class="bi bi-pencil-fill"></i> ' + _('Task updated.'))
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
        return JsonResponse({'success': False, 'error': _('Invalid status')}, status=400)

    task.status = new_status
    task.save()
    return JsonResponse({'success': True, 'new_status_display': task.get_status_display()})


@require_POST
@login_required
def task_delete(request, id):
    task = get_object_or_404(Task, id=id, user=request.user)
    task.delete()
    messages.warning(request, '<i class="bi bi-trash-fill"></i> ' + _('Task deleted.') )
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


TELEGRAM_API = lambda token: f"https://api.telegram.org/bot{token}"

def _send_message(token, chat_id, text, reply_markup=None, parse_mode=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    if parse_mode:
        payload["parse_mode"] = parse_mode
    try:
        requests.post(f"{TELEGRAM_API(token)}/sendMessage", json=payload, timeout=10)
    except Exception as e:
        # при желании логировать
        print("send_message error:", e)

def _answer_callback(token, callback_query_id, text=None, show_alert=False):
    payload = {"callback_query_id": callback_query_id, "show_alert": show_alert}
    if text:
        payload["text"] = text
    try:
        requests.post(f"{TELEGRAM_API(token)}/answerCallbackQuery", json=payload, timeout=10)
    except Exception as e:
        print("answer_callback error:", e)

@csrf_exempt
def telegram_webhook(request, token):
    """
    URL: /bot/<TOKEN>/
    Telegram will POST updates here.
    Мы НЕ используем Application.process_update — обрабатываем update вручную и отправляем ответы через requests.
    """
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if token != bot_token:
        return HttpResponseForbidden("Invalid token")

    if request.method != "POST":
        return JsonResponse({"ok": True})

    try:
        update = json.loads(request.body)
    except Exception:
        return JsonResponse({"ok": False}, status=400)

    # --- message (текстовые команды) ---
    if "message" in update:
        msg = update["message"]
        chat_id = msg.get("chat", {}).get("id")
        text = (msg.get("text") or "").strip()
        
        if not chat_id:
            return JsonResponse({"ok": True})
    
        # всегда генерируем temp_token
        tmp = get_random_string(32)
        profile, _ = TelegramProfile.objects.get_or_create(chat_id=chat_id)
        profile.temp_token = tmp
        profile.save()
        frontend = getattr(settings, "FRONTEND_URL", "")
    
        if text.startswith("/start"):
            if profile.user:
                # уже привязан
                keyboard = {
                    "inline_keyboard": [
                        [{"text": "❌ Отвязать", "callback_data": "unlink"}],
                        [{"text": "🌐 Сменить язык", "callback_data": "change_lang"}]
                    ]
                }
                _send_message(bot_token, chat_id, "Вы уже привязаны. Выберите действие:", reply_markup=keyboard)
            else:
                # не привязан
                link = f"{frontend}/telegram/confirm?token={tmp}&chat_id={chat_id}"
                keyboard = {
                    "inline_keyboard": [
                        [{"text": "🔗 Привязать Telegram", "url": link}],
                        [{"text": "🌐 Сменить язык", "callback_data": "change_lang"}]
                    ]
                }
                _send_message(bot_token, chat_id, "Привет! Нажмите, чтобы привязать аккаунт:", reply_markup=keyboard)
    
        return JsonResponse({"ok": True})

    # --- callback_query (нажатия inline-кнопок) ---
    if "callback_query" in update:
        cq = update["callback_query"]
        data = cq.get("data", "")
        callback_id = cq.get("id")
        message = cq.get("message") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        if not chat_id:
            _answer_callback(bot_token, callback_id, text="Ошибка: не найден chat_id", show_alert=True)
            return JsonResponse({"ok": True})

        if data == "unlink":
            TelegramProfile.objects.filter(chat_id=chat_id).update(user=None, temp_token=None)
            _answer_callback(bot_token, callback_id, text="Вы отвязаны", show_alert=False)

            # отправляем новое сообщение с кнопкой "Привязать"
            tmp = get_random_string(32)
            profile, _ = TelegramProfile.objects.get_or_create(chat_id=chat_id)
            profile.temp_token = tmp
            profile.save()
            frontend = getattr(settings, "FRONTEND_URL", "")
            link = f"{frontend}/telegram/confirm?token={tmp}&chat_id={chat_id}"

            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔗 Привязать Telegram", "url": link}],
                    [{"text": "🌐 Сменить язык", "callback_data": "change_lang"}]
                ]
            }
            _send_message(bot_token, chat_id, "✅ Telegram аккаунт отвязан. Нажмите, чтобы привязать снова:", reply_markup=keyboard)
        elif data == "change_lang":
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🇬🇧 English", "callback_data": "lang:en"}],
                    [{"text": "🇺🇦 Українська", "callback_data": "lang:uk"}],
                    [{"text": "🇷🇺 Русский", "callback_data": "lang:ru"}],
                ]
            }
            _answer_callback(bot_token, callback_id)
            _send_message(bot_token, chat_id, "Выберите язык:", reply_markup=keyboard)
        elif data.startswith("lang:"):
            lang = data.split(":", 1)[1]
            # здесь можно сохранять выбор в профиле или просто информировать
            _answer_callback(bot_token, callback_id, text=f"Язык выбран: {lang}", show_alert=True)
            _send_message(bot_token, chat_id, f"Язык установлен: {lang}. Откройте сайт и проверьте.")
        else:
            _answer_callback(bot_token, callback_id, text="Неизвестная команда", show_alert=True)

        return JsonResponse({"ok": True})

    return JsonResponse({"ok": True})


@csrf_exempt
def confirm_telegram(request):
    """
    Ссылка, на которую ведёт кнопка «Привязать» в боте.
    Если пользователь не залогинен — редиректим на логин и сохраняем токен в сессии.
    После логина пользователь может вернуться на этот URL и мы привяжем аккаунт.
    """
    token = request.GET.get("token")
    chat_id = request.GET.get("chat_id")
    if not token or not chat_id:
        messages.error(request, "Invalid link")
        return redirect("/")

    try:
        profile = TelegramProfile.objects.get(temp_token=token, chat_id=chat_id)
    except TelegramProfile.DoesNotExist:
        messages.error(request, "Invalid or expired token")
        return redirect("/")

    if not request.user.is_authenticated:
        # сохраним данные в сессии и редирект на логин (next оставим на тот же URL)
        request.session['tg_confirm_token'] = token
        request.session['tg_confirm_chat'] = chat_id
        return redirect(f"{settings.LOGIN_URL}?next={request.get_full_path()}")

    # Если пользователь залогинен — связываем профиль
    # Удаляем связь того же chat_id у других записей (на всякий случай)
    TelegramProfile.objects.filter(chat_id=chat_id).exclude(pk=profile.pk).update(user=None)
    profile.user = request.user
    profile.temp_token = None
    profile.save()
    messages.success(request, "✅ Telegram successfully linked!")
    return redirect("/")