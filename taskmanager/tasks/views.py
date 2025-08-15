"""
Views for task management: task CRUD, user registration,
tags autocomplete, and AJAX status update.
"""

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q, Case, When, Value, IntegerField
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from rest_framework import permissions, viewsets

from .forms import TaskForm
from .models import Task, Tag
from .serializers import TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    """DRF viewset for Task model."""
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return tasks for the current authenticated user."""
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Save the task with the current user as owner."""
        serializer.save(user=self.request.user)


def register(request):
    """Register a new user account."""
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
    """Display list of tasks with optional filtering and search."""
    tasks_queryset = Task.objects.filter(user=request.user)
    today = timezone.localdate()

    status_filter = request.GET.get('status')
    query = request.GET.get('q')

    if status_filter:
        tasks_queryset = tasks_queryset.filter(status=status_filter)

    if query:
        tasks_queryset = tasks_queryset.filter(
            Q(title__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()

    tasks_queryset = tasks_queryset.annotate(
        completed_order=Case(
            When(status='completed', then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by('completed_order', 'due_date', '-created_at')

    tasks_list = list(tasks_queryset)
    for task in tasks_list:
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

    return render(
        request,
        'tasks/tasks.html',
        {
            'tasks': tasks_list,
            'status_filter': status_filter,
            'query': query,
        },
    )


@login_required
def task_create(request):
    """Create a new task."""
    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            tags = handle_tags_input(
                form.cleaned_data.get('tags_input', ''),
                request.user,
            )
            task.save()
            task.tags.set(tags)
            form.save_m2m()
            messages.success(
                request,
                '<i class="bi bi-check2"></i> '
                + _('Task successfully created.'),
            )
            return redirect('task_list')
    else:
        form = TaskForm(user=request.user)

    return render(
        request,
        'tasks/task_form.html',
        {
            'form': form,
            'is_edit': False,
        },
    )


@login_required
def task_edit(request, task_id):
    """Edit an existing task."""
    task = get_object_or_404(Task, id=task_id, user=request.user)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()

            tags_input = form.cleaned_data.get('tags_input', '')
            tags = handle_tags_input(tags_input, request.user)
            task.tags.set(tags)

            messages.info(
                request,
                '<i class="bi bi-pencil-fill"></i> ' + _('Task updated.'),
            )
            return redirect('task_list')
    else:
        form = TaskForm(instance=task, user=request.user)

    return render(
        request,
        'tasks/task_form.html',
        {
            'form': form,
            'is_edit': True,
        },
    )


@login_required
@require_POST
def task_update_status_ajax(request, task_id):
    """Update task status via AJAX request."""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    new_status = request.POST.get('status')

    valid_statuses = ['pending', 'in_progress', 'completed']
    if new_status not in valid_statuses:
        return JsonResponse(
            {'success': False, 'error': _('Invalid status')},
            status=400,
        )

    task.status = new_status
    task.save()
    return JsonResponse(
        {
            'success': True,
            'new_status_display': task.get_status_display(),
        }
    )


@login_required
@require_POST
def task_delete(request, task_id):
    """Delete a task."""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    messages.warning(
        request,
        '<i class="bi bi-trash-fill"></i> ' + _('Task deleted.'),
    )
    return redirect('task_list')


def handle_tags_input(tags_str, user):
    """Process comma-separated tags string and return Tag objects."""
    tag_names = [t.strip() for t in tags_str.split(',') if t.strip()]
    tags = []
    for name in tag_names:
        tag, _ = Tag.objects.get_or_create(name=name, user=user)
        tags.append(tag)
    return tags


@login_required
def tag_autocomplete(request):
    """Return JSON list of tag names matching the search term."""
    term = request.GET.get('term', '')
    user = request.user if request.user.is_authenticated else None
    tags = []

    if term and user:
        tags = (
            Tag.objects.filter(name__icontains=term, user=user)
            .values_list('name', flat=True)
            .distinct()
        )

    return JsonResponse(list(tags), safe=False)
