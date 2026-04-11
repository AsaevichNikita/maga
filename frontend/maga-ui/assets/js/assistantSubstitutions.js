(function () {
  window.getAssistantSubstitutions = function () {
    window.makeRequest('GET', '/assistant-substitutions/');
  };

  window.showCreateAssistantSubstitutionForm = function () {
    window.showForm(`
      <h2>Создать подмену ассистента</h2>
      <form onsubmit="event.preventDefault(); createAssistantSubstitution();">
        <div class="form-row">
          <div class="form-group">
            <label>ID группы (group_id) *</label>
            <input type="number" id="sub-group" required>
          </div>
          <div class="form-group">
            <label>Дата занятия *</label>
            <input type="date" id="sub-date" required>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>ID пришедшего ассистента (substitute_assistant_id) *</label>
            <input type="number" id="sub-substitute" required>
          </div>
          <div class="form-group">
            <label>ID заменяемого ассистента (replaced_assistant_id)</label>
            <input type="number" id="sub-replaced" placeholder="может быть пустым">
          </div>
        </div>

        <div class="form-group">
          <label>Комментарий (note)</label>
          <textarea id="sub-note"></textarea>
        </div>

        <div class="form-actions">
          <button type="submit" class="post-btn">Создать подмену</button>
          <button type="button" onclick="hideForms()">Отмена</button>
        </div>
      </form>
    `);
  };

  window.createAssistantSubstitution = function () {
    const replacedVal = document.getElementById('sub-replaced').value;
    const data = {
      group_id: parseInt(document.getElementById('sub-group').value, 10),
      date: document.getElementById('sub-date').value,
      substitute_assistant_id: parseInt(document.getElementById('sub-substitute').value, 10),
      replaced_assistant_id: replacedVal ? parseInt(replacedVal, 10) : null,
      note: document.getElementById('sub-note').value || null
    };
    window.makeRequest('POST', '/assistant-substitutions/', data);
    window.hideForms();
  };

  window.promptGetAssistantSubstitution = function () {
    const id = window.promptId('Введите ID подмены:');
    if (id) window.makeRequest('GET', `/assistant-substitutions/${id}`);
  };

  window.promptUpdateAssistantSubstitution = function () {
    const id = window.promptId('Введите ID подмены для обновления:');
    if (!id) return;

    const note = prompt('Новый note (оставьте пустым):');
    const replaced = prompt('Новый replaced_assistant_id (пусто = не менять, "null" = очистить):');

    const data = {};
    if (note) data.note = note;
    if (replaced) {
      if (replaced === 'null') data.replaced_assistant_id = null;
      else data.replaced_assistant_id = parseInt(replaced, 10);
    }

    if (Object.keys(data).length > 0) {
      window.makeRequest('PUT', `/assistant-substitutions/${id}`, data);
    }
  };

  window.promptDeleteAssistantSubstitution = function () {
    const id = window.promptId('Введите ID подмены для удаления:');
    if (id && confirm(`Удалить подмену ${id}?`)) {
      window.makeRequest('DELETE', `/assistant-substitutions/${id}`);
    }
  };
})();