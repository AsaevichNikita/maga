(function () {
  window.getCourseGroups = function () {
    window.makeRequest('GET', '/course-groups/');
  };

  window.showCreateCourseGroupForm = function () {
    window.showForm(`
      <h2>Создать группу (Course Group)</h2>
      <form onsubmit="event.preventDefault(); createCourseGroup();">
        <div class="form-row">
          <div class="form-group">
            <label>ID курса (course_id) *</label>
            <input type="number" id="group-course" required>
          </div>
          <div class="form-group">
            <label>Название группы *</label>
            <input type="text" id="group-name" required placeholder="например: A / Группа 1">
          </div>
          <div class="form-group">
            <label>Учебный год *</label>
            <input type="text" id="group-year" required placeholder="2025/2026">
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>ID ведущего преподавателя (lead_teacher_id)</label>
            <input type="number" id="group-lead-teacher">
          </div>
          <div class="form-group">
            <label>ID блока информатики (block_id)</label>
            <input type="number" id="group-block">
          </div>
          <div class="form-group">
            <label>Активна</label>
            <select id="group-active">
              <option value="true" selected>true</option>
              <option value="false">false</option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>min_level</label>
            <input type="number" id="group-min-level" min="1" max="10">
          </div>
          <div class="form-group">
            <label>max_level</label>
            <input type="number" id="group-max-level" min="1" max="10">
          </div>
          <div class="form-group">
            <label>max_students_override</label>
            <input type="number" id="group-max-override">
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="post-btn">Создать группу</button>
          <button type="button" onclick="hideForms()">Отмена</button>
        </div>
      </form>
    `);
  };

  window.createCourseGroup = function () {
    const v = (id) => document.getElementById(id).value;
    const n = (x) => x ? parseInt(x, 10) : null;

    const data = {
      course_id: parseInt(v('group-course'), 10),
      name: v('group-name'),
      academic_year: v('group-year'),
      lead_teacher_id: n(v('group-lead-teacher')),
      block_id: n(v('group-block')),
      is_active: document.getElementById('group-active').value === 'true',
      min_level: n(v('group-min-level')),
      max_level: n(v('group-max-level')),
      max_students_override: n(v('group-max-override'))
    };

    window.makeRequest('POST', '/course-groups/', data);
    window.hideForms();
  };

  window.promptGetCourseGroup = function () {
    const id = window.promptId('Введите ID группы:');
    if (id) window.makeRequest('GET', `/course-groups/${id}`);
  };

  window.promptUpdateCourseGroup = function () {
    const id = window.promptId('Введите ID группы для обновления:');
    if (!id) return;

    const name = prompt('Новое имя группы (оставьте пустым):');
    const lead = prompt('Новый lead_teacher_id (оставьте пустым):');
    const active = prompt('Активна? true/false (оставьте пустым):');

    const data = {};
    if (name) data.name = name;
    if (lead) data.lead_teacher_id = parseInt(lead, 10);
    if (active) data.is_active = active === 'true';

    if (Object.keys(data).length > 0) {
      window.makeRequest('PUT', `/course-groups/${id}`, data);
    }
  };

  window.promptDeleteCourseGroup = function () {
    const id = window.promptId('Введите ID группы для удаления:');
    if (id && confirm(`Удалить группу ${id}?`)) {
      window.makeRequest('DELETE', `/course-groups/${id}`);
    }
  };
})();