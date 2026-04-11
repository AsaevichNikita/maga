(function () {
  window.getCourseCategories = function () {
    window.makeRequest('GET', '/course-categories/');
  };

  window.showCreateCourseCategoryForm = function () {
    window.showForm(`
      <h2>Создать направление (Course Category)</h2>
      <form onsubmit="event.preventDefault(); createCourseCategory();">
        <div class="form-row">
          <div class="form-group">
            <label>Название *</label>
            <input type="text" id="cat-name" required>
          </div>
          <div class="form-group">
            <label>Уровень образования (education_level)</label>
            <select id="cat-edu">
              <option value="">(пусто)</option>
              <option value="дошкольное">дошкольное</option>
              <option value="школьное">школьное</option>
              <option value="среднее_профессиональное">среднее_профессиональное</option>
              <option value="высшее">высшее</option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>min_grade</label>
            <input type="number" id="cat-min-grade">
          </div>
          <div class="form-group">
            <label>max_grade</label>
            <input type="number" id="cat-max-grade">
          </div>
          <div class="form-group">
            <label>min_age</label>
            <input type="number" id="cat-min-age">
          </div>
          <div class="form-group">
            <label>max_age</label>
            <input type="number" id="cat-max-age">
          </div>
        </div>

        <div class="form-group">
          <label>Описание</label>
          <textarea id="cat-desc"></textarea>
        </div>

        <div class="form-actions">
          <button type="submit" class="post-btn">Создать направление</button>
          <button type="button" onclick="hideForms()">Отмена</button>
        </div>
      </form>
    `);
  };

  window.createCourseCategory = function () {
    const val = (id) => document.getElementById(id).value;
    const n = (x) => x ? parseInt(x, 10) : null;

    const data = {
      name: val('cat-name'),
      description: val('cat-desc') || null,
      min_grade: n(val('cat-min-grade')),
      max_grade: n(val('cat-max-grade')),
      min_age: n(val('cat-min-age')),
      max_age: n(val('cat-max-age')),
      education_level: val('cat-edu') || null
    };

    window.makeRequest('POST', '/course-categories/', data);
    window.hideForms();
  };

  window.promptGetCourseCategory = function () {
    const id = window.promptId('Введите ID направления:');
    if (id) window.makeRequest('GET', `/course-categories/${id}`);
  };

  window.promptUpdateCourseCategory = function () {
    const id = window.promptId('Введите ID направления для обновления:');
    if (!id) return;

    const name = prompt('Новое название (оставьте пустым):');
    const desc = prompt('Новое описание (оставьте пустым):');

    const data = {};
    if (name) data.name = name;
    if (desc) data.description = desc;

    if (Object.keys(data).length > 0) {
      window.makeRequest('PUT', `/course-categories/${id}`, data);
    }
  };

  window.promptDeleteCourseCategory = function () {
    const id = window.promptId('Введите ID направления для удаления:');
    if (id && confirm(`Удалить направление ${id}?`)) {
      window.makeRequest('DELETE', `/course-categories/${id}`);
    }
  };
})();