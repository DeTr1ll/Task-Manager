document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.list-group-item').forEach(item => {
      item.addEventListener('click', function (e) {
        if (e.target.closest('button') || e.target.closest('a')) return;

        const desc = this.querySelector('.task-description');
        if (desc) {
          desc.classList.toggle('expanded');
        }
      });
    });
});
