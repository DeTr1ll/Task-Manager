from datetime import timedelta
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from rest_framework import viewsets, permissions

from .forms import TaskForm
from .models import Task, Tag
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
    tasks = tasks.order_by('-created_at')

    for task in tasks:
        if task.due_date and task.status != 'completed':
            if task.due_date < today:
                task.highlight = 'danger'
            elif task.due_date <= today + timedelta(days=2):
                task.highlight = 'warning'
            else:
                task.highlight = ''
        else:
            task.highlight = 'success'

    return render(request, 'tasks/tasks.html', {
        'tasks': tasks,
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
            messages.success(request, '✅ Задачу успішно створено.')
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

            messages.info(request, '✏️ Задачу оновлено.')
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

@login_required
def task_delete(request, id):
    task = get_object_or_404(Task, id=id, user=request.user)
    task.delete()
    messages.warning(request, '🗑️ Задачу видалено.')
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