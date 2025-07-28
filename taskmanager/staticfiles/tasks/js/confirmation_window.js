document.addEventListener('DOMContentLoaded', () => {
  const deleteButtons = document.querySelectorAll('.delete-task-btn');
  const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
  const deleteModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));

  deleteButtons.forEach(button => {
    button.addEventListener('click', () => {
      const taskId = button.getAttribute('data-task-id');
      confirmDeleteBtn.setAttribute('data-task-id', taskId);
      deleteModal.show();
    });
  });

  confirmDeleteBtn.addEventListener('click', () => {
    const taskId = confirmDeleteBtn.getAttribute('data-task-id');
    if (!taskId) return;

    fetch(`/delete/${taskId}/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
      }
    })
    .then(response => {
      if (!response.ok) throw new Error('Помилка при видаленні задачі');

      const taskElement = document.getElementById(`task-${taskId}`);
      if (taskElement) {
        taskElement.remove();
      } else {
        console.warn(`Елемент task-${taskId} не найден для удаления`);
      }
      deleteModal.hide();
    })
    .catch(error => alert(error.message));
  });

  function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split(';') : [];
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + '=')) {
        return decodeURIComponent(cookie.substring(name.length + 1));
      }
    }
    return null;
  }
});
