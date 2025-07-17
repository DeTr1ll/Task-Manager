from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import TaskForm
from .models import Task
from django.contrib import messages


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

    status_filter = request.GET.get('status')
    query = request.GET.get('q')

    if status_filter:
        tasks = tasks.filter(status=status_filter)

    if query:
        tasks = tasks.filter(title__icontains=query)

    tasks = tasks.order_by('-created_at')

    return render(request, 'tasks/tasks.html', {
        'tasks': tasks,
        'status_filter': status_filter,
        'query': query,
    })

@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, '✅ Задачу успішно створено.')
            return redirect('task_list')
    else:
        form = TaskForm()
    
    return render(request, 'tasks/task_form.html', {'form': form, 'is_edit': False})

@login_required
def task_edit(request, id):
    task = get_object_or_404(Task, id=id, user=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            messages.info(request, '✏️ Задачу оновлено.')
            return redirect('task_list')
    else:
        form = TaskForm(instance=task)
    
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
