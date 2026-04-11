(function () {
  window.getSchedule = function () {
    window.makeRequest('GET', '/schedule/');
  };

  window.showCreateSlotForm = function () {
    window.showForm(`
      <h2>Создать новый слот расписания</h2>
      <form onsubmit="event.preventDefault(); createSlot();">
        <div class="form-row">
          <div class="form-group">
            <label>ID группы (group_id) *</label>
            <input type="number" id="slot-group" required>
          </div>
          <div class="form-group">
            <label>День недели * (1-7)</label>
            <input type="number" id="slot-day" min="1" max="7" required>
          </div>
          <div class="form-group">
            <label>ID аудитории (classroom_id)</label>
            <input type="number" id="slot-classroom-id" placeholder="например: 1">
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>Время начала * (ЧЧ:ММ)</label>
            <input type="time" id="slot-start" required>
          </div>
          <div class="form-group">
            <label>Время окончания * (ЧЧ:ММ)</label>
            <input type="time" id="slot-end" required>
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="post-btn">Создать слот</button>
          <button type="button" onclick="hideForms()">Отмена</button>
        </div>
      </form>
    `);
  };

  window.createSlot = function () {
    const classroomIdVal = document.getElementById('slot-classroom-id').value;
    const data = {
      group_id: parseInt(document.getElementById('slot-group').value, 10),
      day_of_week: parseInt(document.getElementById('slot-day').value, 10),
      start_time: document.getElementById('slot-start').value.slice(0, 5),
      end_time: document.getElementById('slot-end').value.slice(0, 5)
    };
    if (classroomIdVal) data.classroom_id = parseInt(classroomIdVal, 10);

    window.makeRequest('POST', '/schedule/', data);
    window.hideForms();
  };

  window.promptGetSlot = function () {
    const slotId = window.promptId('Введите ID слота:');
    if (slotId) window.makeRequest('GET', `/schedule/${slotId}`);
  };

  window.promptUpdateSlot = function () {
    const slotId = window.promptId('Введите ID слота для обновления:');
    if (!slotId) return;

    const classroomId = prompt('Новый classroom_id (оставьте пустым, чтобы не менять):');
    const day = prompt('Новый день недели 1-7 (оставьте пустым):');
    const time = prompt('Новое время (ЧЧ:ММ-ЧЧ:ММ) или оставьте пустым:');

    const data = {};
    if (classroomId) data.classroom_id = parseInt(classroomId, 10);
    if (day) data.day_of_week = parseInt(day, 10);
    if (time) {
      const parts = time.split('-').map((s) => (s || '').trim());
      if (parts[0]) data.start_time = parts[0];
      if (parts[1]) data.end_time = parts[1];
    }

    if (Object.keys(data).length > 0) {
      window.makeRequest('PUT', `/schedule/${slotId}`, data);
    }
  };

  window.promptDeleteSlot = function () {
    const slotId = window.promptId('Введите ID слота для удаления:');
    if (slotId && confirm(`Удалить слот ${slotId}?`)) {
      window.makeRequest('DELETE', `/schedule/${slotId}`);
    }
  };

  window.getMyTeacherProfile = function () {
    window.makeRequest('GET', '/teachers/me');
  };

  window.getMyTeacherSchedule = function () {
    window.makeRequest('GET', '/teachers/me/schedule');
  };
})();
