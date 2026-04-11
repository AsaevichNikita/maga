(function () {
  window.getTeachers = function () {
    window.makeRequest('GET', '/teachers/');
  };

  window.showCreateTeacherForm = function () {
    window.showForm(`
      <h2>Создать преподавателя</h2>
      <form onsubmit="event.preventDefault(); createTeacher();">
        <div class="form-row">
          <div class="form-group">
            <label>Имя *</label>
            <input type="text" id="teacher-firstname" required>
          </div>
          <div class="form-group">
            <label>Фамилия *</label>
            <input type="text" id="teacher-lastname" required>
          </div>
          <div class="form-group">
            <label>Отчество</label>
            <input type="text" id="teacher-surname">
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>Дата рождения * (ГГГГ-ММ-ДД)</label>
            <input type="date" id="teacher-birthday" required>
          </div>
          <div class="form-group">
            <label>Телефон</label>
            <input type="tel" id="teacher-phone">
          </div>
          <div class="form-group">
            <label>Email *</label>
            <input type="email" id="teacher-email" required>
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="post-btn">Создать преподавателя</button>
          <button type="button" onclick="hideForms()">Отмена</button>
        </div>
      </form>
    `);
  };

  window.createTeacher = function () {
    const data = {
      firstname: document.getElementById('teacher-firstname').value,
      lastname: document.getElementById('teacher-lastname').value,
      surname: document.getElementById('teacher-surname').value || null,
      birthday: document.getElementById('teacher-birthday').value,
      phone_number: document.getElementById('teacher-phone').value || null,
      email: document.getElementById('teacher-email').value
    };

    window.makeRequest('POST', '/teachers/', data);
    window.hideForms();
  };

  window.promptGetTeacher = function () {
    const teacherId = window.promptId('Введите ID преподавателя:');
    if (teacherId) window.makeRequest('GET', `/teachers/${teacherId}`);
  };

  window.promptUpdateTeacher = function () {
    const teacherId = window.promptId('Введите ID преподавателя для обновления:');
    if (!teacherId) return;

    const firstname = prompt('Новое имя (оставьте пустым, чтобы не менять):');
    const lastname = prompt('Новая фамилия (оставьте пустым, чтобы не менять):');
    const surname = prompt('Новое отчество (оставьте пустым, чтобы не менять):');
    const birthday = prompt('Новая дата рождения (YYYY-MM-DD) (оставьте пустым, чтобы не менять):');
    const phone = prompt('Новый телефон (оставьте пустым, чтобы не менять):');
    const email = prompt('Новый email (оставьте пустым, чтобы не менять):');

    const data = {};
    if (firstname) data.firstname = firstname;
    if (lastname) data.lastname = lastname;
    if (surname) data.surname = surname;
    if (birthday) data.birthday = birthday;
    if (phone) data.phone_number = phone;
    if (email) data.email = email;

    if (Object.keys(data).length > 0) {
      window.makeRequest('PUT', `/teachers/${teacherId}`, data);
    }
  };

  window.promptDeleteTeacher = function () {
    const teacherId = window.promptId('Введите ID преподавателя для удаления:');
    if (teacherId && confirm(`Удалить преподавателя ${teacherId}?`)) {
      window.makeRequest('DELETE', `/teachers/${teacherId}`);
    }
  };

  window.getMyTeacherProfile = function () {
    window.makeRequest('GET', '/teachers/me');
  };
})();