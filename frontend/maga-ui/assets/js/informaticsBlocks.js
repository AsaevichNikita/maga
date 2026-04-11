(function () {
  window.getInformaticsBlocks = function () {
    window.makeRequest('GET', '/informatics-blocks/');
  };

  window.showCreateInformaticsBlockForm = function () {
    window.showForm(`
      <h2>Создать блок информатики</h2>
      <form onsubmit="event.preventDefault(); createInformaticsBlock();">
        <div class="form-row">
          <div class="form-group">
            <label>ID курса (course_id) *</label>
            <input type="number" id="block-course" required>
          </div>
          <div class="form-group">
            <label>Название *</label>
            <input type="text" id="block-name" required>
          </div>
        </div>

        <div class="form-group">
          <label>Описание</label>
          <textarea id="block-desc"></textarea>
        </div>

        <div class="form-group">
          <label>Skills (через запятую)</label>
          <input type="text" id="block-skills" placeholder="python, arrays, loops">
        </div>

        <div class="form-actions">
          <button type="submit" class="post-btn">Создать блок</button>
          <button type="button" onclick="hideForms()">Отмена</button>
        </div>
      </form>
    `);
  };

  window.createInformaticsBlock = function () {
    const skills = window.parseCsvStrings(document.getElementById('block-skills').value);
    const data = {
      course_id: parseInt(document.getElementById('block-course').value, 10),
      name: document.getElementById('block-name').value,
      description: document.getElementById('block-desc').value || null,
      skills: skills.length > 0 ? skills : []
    };
    window.makeRequest('POST', '/informatics-blocks/', data);
    window.hideForms();
  };

  window.promptGetInformaticsBlock = function () {
    const id = window.promptId('Введите ID блока:');
    if (id) window.makeRequest('GET', `/informatics-blocks/${id}`);
  };

  window.promptUpdateInformaticsBlock = function () {
    const id = window.promptId('Введите ID блока для обновления:');
    if (!id) return;

    const name = prompt('Новое название (оставьте пустым):');
    const skillsCsv = prompt('Новые skills (через запятую, пусто = не менять):');

    const data = {};
    if (name) data.name = name;
    if (skillsCsv) data.skills = window.parseCsvStrings(skillsCsv);

    if (Object.keys(data).length > 0) {
      window.makeRequest('PUT', `/informatics-blocks/${id}`, data);
    }
  };

  window.promptDeleteInformaticsBlock = function () {
    const id = window.promptId('Введите ID блока для удаления:');
    if (id && confirm(`Удалить блок ${id}?`)) {
      window.makeRequest('DELETE', `/informatics-blocks/${id}`);
    }
  };
})();