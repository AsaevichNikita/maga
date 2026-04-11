(function () {
  window.getStudents = function () {
    window.makeRequest('GET', '/students/');
  };

  window.showCreateStudentForm = function () {
    window.showForm(`
      <h2>Создать нового студента</h2>
      <form onsubmit="event.preventDefault(); createStudent();">
        <div class="form-row">
          <div class="form-group">
            <label>Имя *</label>
            <input type="text" id="student-firstname" required>
          </div>
          <div class="form-group">
            <label>Фамилия *</label>
            <input type="text" id="student-lastname" required>
          </div>
          <div class="form-group">
            <label>Отчество</label>
            <input type="text" id="student-surname">
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>Дата рождения * (ГГГГ-ММ-ДД)</label>
            <input type="date" id="student-birthday" required>
          </div>
          <div class="form-group">
            <label>Телефон</label>
            <input type="tel" id="student-phone">
          </div>
          <div class="form-group">
            <label>Email</label>
            <input type="email" id="student-email">
          </div>
        </div>

        <div class="form-group">
          <label>Адрес *</label>
          <input type="text" id="student-address" required>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>Учебное заведение *</label>
            <input type="text" id="student-institution" required>
          </div>
          <div class="form-group">
            <label>Группа/класс *</label>
            <input type="text" id="student-group" required>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>Тип обучения *</label>
            <select id="student-edu-type" required>
              <option value="">Выберите тип</option>
              <option value="дошкольное">дошкольное</option>
              <option value="школьное">школьное</option>
              <option value="среднее_профессиональное">среднее_профессиональное</option>
              <option value="высшее">высшее</option>
            </select>
          </div>
          <div class="form-group">
            <label>
              <input type="checkbox" id="student-enrolled"> Зачислен в этом году
            </label>
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="post-btn">Создать студента</button>
          <button type="button" onclick="hideForms()">Отмена</button>
        </div>
      </form>
    `);
  };

  window.createStudent = function () {
    const data = {
      firstname: document.getElementById('student-firstname').value,
      lastname: document.getElementById('student-lastname').value,
      surname: document.getElementById('student-surname').value || null,
      phone_number: document.getElementById('student-phone').value || null,
      email: document.getElementById('student-email').value || null,
      birthday: document.getElementById('student-birthday').value,
      address: document.getElementById('student-address').value,
      educational_institution: document.getElementById('student-institution').value,
      group_name: document.getElementById('student-group').value,
      education_type: document.getElementById('student-edu-type').value,
      enrolled_this_year: document.getElementById('student-enrolled').checked
    };

    window.makeRequest('POST', '/students/', data);
    window.hideForms();
  };

  window.promptGetStudent = function () {
    const studentId = window.promptId('Введите ID студента:');
    if (studentId) window.makeRequest('GET', `/students/${studentId}`);
  };

  window.promptUpdateStudent = function () {
    const studentId = window.promptId('Введите ID студента для обновления:');
    if (!studentId) return;

    const phone = prompt('Новый телефон (оставьте пустым, чтобы не менять):');
    const email = prompt('Новый email (оставьте пустым, чтобы не менять):');
    const address = prompt('Новый адрес (оставьте пустым):');

    const data = {};
    if (phone) data.phone_number = phone;
    if (email) data.email = email;
    if (address) data.address = address;

    if (Object.keys(data).length > 0) {
      window.makeRequest('PUT', `/students/${studentId}`, data);
    }
  };

  window.promptDeleteStudent = function () {
    const studentId = window.promptId('Введите ID студента для удаления:');
    if (studentId && confirm(`Удалить студента ${studentId}?`)) {
      window.makeRequest('DELETE', `/students/${studentId}`);
    }
  };
})();