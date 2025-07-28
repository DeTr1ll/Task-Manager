document.addEventListener('DOMContentLoaded', function () {
  const statusButtons = document.querySelectorAll('.status-btns button');

  statusButtons.forEach(button => {
    button.addEventListener('click', function () {
      const newStatus = this.getAttribute('data-status');
      const taskId = this.parentElement.getAttribute('data-task-id');

      updateTaskStatus(taskId, newStatus);
    });
  });

  function updateTaskStatus(taskId, newStatus) {
    fetch(`/${taskId}/update-status/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: `status=${newStatus}`
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          const taskElement = document.getElementById(`task-${taskId}`);
          const dueDateStr = taskElement.getAttribute('data-due-date');

          updateStatusText(taskId, data.new_status_display);
          updateStatusButtons(taskId, newStatus);
          updateDueDateColor(taskElement, dueDateStr, newStatus);
          reorderTask(taskElement, newStatus, dueDateStr);
        } else {
          alert('Помилка зміни статусу: ' + data.error);
        }
      });
  }

  function updateStatusText(taskId, statusText) {
    const statusDisplay = document.querySelector(`#task-${taskId} .status-display`);
    if (statusDisplay) {
      statusDisplay.textContent = statusText;
    }
  }

  function updateStatusButtons(taskId, newStatus) {
    const btnGroup = document.querySelector(`#task-${taskId} .status-btns`);
    const buttons = btnGroup.querySelectorAll('button');

    const statusClasses = {
      pending: ['btn-secondary', 'btn-outline-secondary'],
      in_progress: ['btn-warning', 'btn-outline-warning'],
      completed: ['btn-success', 'btn-outline-success']
    };

    buttons.forEach(btn => {
      const btnStatus = btn.getAttribute('data-status');

      // Удаляем все возможные классы
      Object.values(statusClasses).flat().forEach(cls => btn.classList.remove(cls));

      // Назначаем новый класс
      if (btnStatus === newStatus) {
        btn.classList.add(statusClasses[btnStatus][0]);
      } else {
        btn.classList.add(statusClasses[btnStatus][1]);
      }
    });
  }

  function updateDueDateColor(taskElement, dueDateStr, newStatus) {
    const dueDateElem = taskElement.querySelector('.due-date-display');
    if (!dueDateElem) return;

    dueDateElem.classList.remove('text-danger', 'text-warning', 'text-muted');

    if (newStatus === 'completed') {
      dueDateElem.classList.add('text-muted');
      return;
    }

    if (dueDateStr) {
      const dueDate = new Date(dueDateStr);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      dueDate.setHours(0, 0, 0, 0);

      const diffDays = Math.floor((dueDate - today) / (1000 * 60 * 60 * 24));

      if (diffDays < 0) {
        dueDateElem.classList.add('text-danger');
      } else if (diffDays <= 0) {
        dueDateElem.classList.add('text-warning');
      } else {
        dueDateElem.classList.add('text-muted');
      }
    }
  }

  function reorderTask(taskElement, newStatus, dueDateStr) {
    const listGroup = taskElement.parentElement;
    taskElement.setAttribute('data-status', newStatus);
    
    const hasDueDate = Boolean(dueDateStr);
    const taskDueDate = hasDueDate ? new Date(dueDateStr) : null;
    if (taskDueDate) taskDueDate.setHours(0, 0, 0, 0); // сброс времени
    
    if (newStatus === 'completed') {
      listGroup.appendChild(taskElement);
      taskElement.classList.add('list-group-item-success');
      return;
    }
  
    taskElement.classList.remove('list-group-item-success');
  
    const tasks = Array.from(listGroup.children);
    let inserted = false;
  
    for (const el of tasks) {
      const status = el.getAttribute('data-status');
      if (status === 'completed') continue;
    
      const elDueDateStr = el.getAttribute('data-due-date');
      const elHasDueDate = Boolean(elDueDateStr);
      const elDueDate = elHasDueDate ? new Date(elDueDateStr) : null;
      if (elDueDate) elDueDate.setHours(0, 0, 0, 0); // сброс времени
    
      // Логика вставки
      if (hasDueDate && !elHasDueDate) {
        listGroup.insertBefore(taskElement, el);
        inserted = true;
        break;
      }
    
      if (hasDueDate && elHasDueDate && taskDueDate < elDueDate) {
        listGroup.insertBefore(taskElement, el);
        inserted = true;
        break;
      }
    }
  
    if (!inserted) {
      const firstCompleted = tasks.find(el => el.getAttribute('data-status') === 'completed');
      if (firstCompleted) {
        listGroup.insertBefore(taskElement, firstCompleted);
      } else {
        listGroup.appendChild(taskElement);
      }
    }
  }

  function getCookie(name) {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + '=')) {
        return decodeURIComponent(cookie.substring(name.length + 1));
      }
    }
    return null;
  }
});
