document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('tags-input');
  if (!input) {
    console.log('⚠️ Поле #tags-input не найдено');
    return;
  }
  const suggestionsBox = document.getElementById('tag-suggestions');

  input.addEventListener('input', async () => {
    console.log('🔍 Input changed:', input.value);
    const currentText = input.value;
    const parts = currentText.split(',');
    const lastTerm = parts[parts.length - 1].trim();

    if (lastTerm.length < 1) {
      suggestionsBox.innerHTML = '';
      return;
    }

    const response = await fetch(`/tasks/tags/autocomplete/?term=${encodeURIComponent(lastTerm)}`);
    const suggestions = await response.json();

    suggestionsBox.innerHTML = '';
    suggestions.forEach(tag => {
      const item = document.createElement('button');
      item.className = 'list-group-item list-group-item-action';
      item.textContent = tag;
      item.type = 'button';
      item.onclick = () => {
        parts[parts.length - 1] = tag;
        input.value = parts.join(', ') + ', ';
        suggestionsBox.innerHTML = '';
        input.focus();
      };
      suggestionsBox.appendChild(item);
    });
  });

  // Скрыть подсказки при клике вне
  document.addEventListener('click', (e) => {
    if (!suggestionsBox.contains(e.target) && e.target !== input) {
      suggestionsBox.innerHTML = '';
    }
  });
});
