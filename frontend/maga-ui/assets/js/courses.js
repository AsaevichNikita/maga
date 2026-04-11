(function () {
  window.getCourses = function () {
    window.makeRequest('GET', '/courses/');
  };

  window.showCreateCourseForm = function () {
    window.showForm(`
      <h2>Создать новый курс</h2>
      <form onsubmit="event.preventDefault(); createCourse();">
        <div class="form-row">
          <div class="form-group">
            <label>Название курса *</label>
            <input type="text" id="course-name" required>
          </div>
          <div class="form-group">
            <label>ID направления (category_id)</label>
            <input type="number" id="course-category">
          </div>
          <div class="form-group">
            <label>Преподаватели (ID через запятую)</label>
            <input type="text" id="course-teachers" placeholder="например: 1,2,5">
            <div class="small-hint">Отправим как allowed_teacher_ids: [..] (если бэк поддерживает)</div>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>Макс. студентов</label>
            <input type="number" id="course-max" value="15">
          </div>
          <div class="form-group">
            <label>Использовать вместимость аудитории</label>
            <select id="course-use-capacity">
              <option value="false" selected>false</option>
              <option value="true">true</option>
            </select>
          </div>
          <div class="form-group">
            <label>Длительность (мин)</label>
            <input type="number" id="course-duration" value="90">
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>Цена</label>
            <input type="number" step="0.01" id="course-price" value="0">
          </div>
          <div class="form-group">
            <label>Активен</label>
            <select id="course-active">
              <option value="true" selected>true</option>
              <option value="false">false</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label>Описание</label>
          <textarea id="course-description"></textarea>
        </div>

        <div class="form-actions">
          <button type="submit" class="post-btn">Создать курс</button>
          <button type="button" onclick="hideForms()">Отмена</button>
        </div>
      </form>
    `);
  };

  window.createCourse = function () {
    const teachersCsv = document.getElementById('course-teachers').value;
    const allowedTeacherIds = window.parseCsvNumbers(teachersCsv);

    const categoryVal = document.getElementById('course-category').value;
    const data = {
      name: document.getElementById('course-name').value,
      category_id: categoryVal ? parseInt(categoryVal, 10) : null,
      max_students: parseInt(document.getElementById('course-max').value, 10),
      use_classroom_capacity: document.getElementById('course-use-capacity').value === 'true',
      duration_minutes: parseInt(document.getElementById('course-duration').value, 10),
      price: parseFloat(document.getElementById('course-price').value),
      description: document.getElementById('course-description').value || null,
      is_active: document.getElementById('course-active').value === 'true'
    };

    if (allowedTeacherIds.length > 0) data.allowed_teacher_ids = allowedTeacherIds;

    window.makeRequest('POST', '/courses/', data);
    window.hideForms();
  };

  window.promptGetCourse = function () {
    const courseId = window.promptId('Введите ID курса:');
    if (courseId) window.makeRequest('GET', `/courses/${courseId}`);
  };

  window.promptUpdateCourse = function () {
    const courseId = window.promptId('Введите ID курса для обновления:');
    if (!courseId) return;

    const name = prompt('Новое название (оставьте пустым, чтобы не менять):');
    const max = prompt('Макс. студентов (оставьте пустым, чтобы не менять):');
    const active = prompt('Активен? true/false (оставьте пустым):');

    const data = {};
    if (name) data.name = name;
    if (max) data.max_students = parseInt(max, 10);
    if (active) data.is_active = active === 'true';

    if (Object.keys(data).length > 0) {
      window.makeRequest('PUT', `/courses/${courseId}`, data);
    }
  };

  window.promptDeleteCourse = function () {
    const courseId = window.promptId('Введите ID курса для удаления:');
    if (courseId && confirm(`Удалить курс ${courseId}?`)) {
      window.makeRequest('DELETE', `/courses/${courseId}`);
    }
  };
})();