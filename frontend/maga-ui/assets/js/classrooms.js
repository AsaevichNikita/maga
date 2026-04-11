(function () {
  window.getClassrooms = function () {
    window.makeRequest('GET', '/classrooms/');
  };

  window.showCreateClassroomForm = function () {
    window.showForm(`
      <h2>Создать аудиторию</h2>
      <form onsubmit="event.preventDefault(); createClassroom();">
        <div class="form-row">
          <div class="form-group">
            <label>Название *</label>
            <input type="text" id="classroom-name" required placeholder="например: 101 / Кабинет 3">
          </div>
          <div class="form-group">
            <label>Вместимость</label>
            <input type="number" id="classroom-capacity" value="15">
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="post-btn">Создать аудиторию</button>
          <button type="button" onclick="hideForms()">Отмена</button>
        </div>
      </form>
    `);
  };

  window.createClassroom = function () {
    const data = {
      name: document.getElementById('classroom-name').value,
      capacity: parseInt(document.getElementById('classroom-capacity').value, 10)
    };
    window.makeRequest('POST', '/classrooms/', data);
    window.hideForms();
  };

  window.promptGetClassroom = function () {
    const id = window.promptId('Введите ID аудитории:');
    if (id) window.makeRequest('GET', `/classrooms/${id}`);
  };

  window.promptUpdateClassroom = function () {
    const id = window.promptId('Введите ID аудитории для обновления:');
    if (!id) return;

    const name = prompt('Новое имя (оставьте пустым):');
    const cap = prompt('Новая вместимость (оставьте пустым):');

    const data = {};
    if (name) data.name = name;
    if (cap) data.capacity = parseInt(cap, 10);

    if (Object.keys(data).length > 0) {
      window.makeRequest('PUT', `/classrooms/${id}`, data);
    }
  };

  window.promptDeleteClassroom = function () {
    const id = window.promptId('Введите ID аудитории для удаления:');
    if (id && confirm(`Удалить аудиторию ${id}?`)) {
      window.makeRequest('DELETE', `/classrooms/${id}`);
    }
  };
})();