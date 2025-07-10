document.addEventListener('DOMContentLoaded', function () {
  const statusButtons = document.querySelectorAll('.status-btns button');

  statusButtons.forEach(button => {
    button.addEventListener('click', function () {
      const newStatus = this.getAttribute('data-status');
      const taskId = this.parentElement.getAttribute('data-task-id');

      fetch(`/tasks/${taskId}/update-status/`, {
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
            // Обновляем текст статуса
            const statusText = document.querySelector(`#task-${taskId} .status-display`);
            if (statusText) {
              statusText.textContent = `Статус: ${data.new_status_display}`;
            }

            // Обновляем подсветку кнопок
            const btnGroup = document.querySelector(`#task-${taskId} .status-btns`);
            const buttons = btnGroup.querySelectorAll('button');

            buttons.forEach(btn => {
              // Убираем все активные стили
              btn.classList.remove('btn-secondary', 'btn-warning', 'btn-success');
              btn.classList.remove('btn-outline-secondary', 'btn-outline-warning', 'btn-outline-success');

              const btnStatus = btn.getAttribute('data-status');
              if (btnStatus === newStatus) {
                // Подсвечиваем текущую кнопку
                if (btnStatus === 'pending') btn.classList.add('btn-secondary');
                if (btnStatus === 'in_progress') btn.classList.add('btn-warning');
                if (btnStatus === 'completed') btn.classList.add('btn-success');
              } else {
                // Остальные кнопки — неактивны
                if (btnStatus === 'pending') btn.classList.add('btn-outline-secondary');
                if (btnStatus === 'in_progress') btn.classList.add('btn-outline-warning');
                if (btnStatus === 'completed') btn.classList.add('btn-outline-success');
              }
            });
          } else {
            alert('Помилка зміни статусу: ' + data.error);
          }
        });
    });
  });

  // CSRF-токен из cookie
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
});
