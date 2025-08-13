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
from django.http import JsonResponse
import json
import asyncio
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from tg_bot.settings import TELEGRAM_TOKEN
from telegram import Update
from tg_bot.main import application
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model

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


@csrf_exempt
def telegram_webhook(request, token):
    from telegram import Update

    if token != application.bot.token:
        return JsonResponse({"ok": False, "error": "Invalid token"}, status=403)

    data = json.loads(request.body)
    update = Update.de_json(data, application.bot)

    # запускаем синхронно обработку update
    async_to_sync(application.process_update)(update)
    return JsonResponse({"ok": True})

User = get_user_model()

@csrf_exempt
def confirm_telegram(request):
    token = request.GET.get("token")
    chat_id = request.GET.get("chat_id")

    if not token or not chat_id:
        return JsonResponse({"ok": False, "error": "Missing token or chat_id"}, status=400)

    try:
        user = User.objects.get(telegram_token=token)  # поле telegram_token нужно добавить в модель User
    except User.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Invalid token"}, status=404)

    TelegramProfile.objects.update_or_create(user=user, defaults={"chat_id": chat_id})

    return JsonResponse({"ok": True, "message": "Telegram confirmed"})