(function () {
  window.getAssistants = function () {
    window.makeRequest('GET', '/assistants/');
  };

  window.showCreateAssistantForm = function () {
    window.showForm(`
      <h2>Создать ассистента</h2>
      <form onsubmit="event.preventDefault(); createAssistant();">
        <div class="form-row">
          <div class="form-group">
            <label>Имя *</label>
            <input type="text" id="assistant-firstname" required>
          </div>
          <div class="form-group">
            <label>Фамилия *</label>
            <input type="text" id="assistant-lastname" required>
          </div>
          <div class="form-group">
            <label>Отчество</label>
            <input type="text" id="assistant-surname">
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>Дата рождения * (ГГГГ-ММ-ДД)</label>
            <input type="date" id="assistant-birthday" required>
          </div>
          <div class="form-group">
            <label>Телефон *</label>
            <input type="tel" id="assistant-phone" required>
          </div>
          <div class="form-group">
            <label>Email</label>
            <input type="email" id="assistant-email" placeholder="может быть пустым">
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="post-btn">Создать ассистента</button>
          <button type="button" onclick="hideForms()">Отмена</button>
        </div>
      </form>
    `);
  };

  window.createAssistant = function () {
    const data = {
      firstname: document.getElementById('assistant-firstname').value,
      lastname: document.getElementById('assistant-lastname').value,
      surname: document.getElementById('assistant-surname').value || null,
      birthday: document.getElementById('assistant-birthday').value,
      phone_number: document.getElementById('assistant-phone').value,
      email: document.getElementById('assistant-email').value || null
    };
    window.makeRequest('POST', '/assistants/', data);
    window.hideForms();
  };

  window.promptGetAssistant = function () {
    const id = window.promptId('Введите ID ассистента:');
    if (id) window.makeRequest('GET', `/assistants/${id}`);
  };

  window.promptUpdateAssistant = function () {
    const id = window.promptId('Введите ID ассистента для обновления:');
    if (!id) return;

    const phone = prompt('Новый телефон (оставьте пустым, чтобы не менять):');
    const email = prompt('Новый email (оставьте пустым, чтобы не менять):');

    const data = {};
    if (phone) data.phone_number = phone;
    if (email) data.email = email;

    if (Object.keys(data).length > 0) {
      window.makeRequest('PUT', `/assistants/${id}`, data);
    }
  };

  window.promptDeleteAssistant = function () {
    const id = window.promptId('Введите ID ассистента для удаления:');
    if (id && confirm(`Удалить ассистента ${id}?`)) {
      window.makeRequest('DELETE', `/assistants/${id}`);
    }
  };
})();