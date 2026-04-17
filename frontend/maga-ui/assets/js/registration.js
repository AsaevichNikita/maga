(function () {
  function isAuthenticated() {
    const token = typeof window.getAccessToken === 'function'
      ? window.getAccessToken()
      : (localStorage.getItem('access_token') || localStorage.getItem('token'));

    const user = typeof window.getCurrentAuthUser === 'function'
      ? window.getCurrentAuthUser()
      : null;

    return Boolean(token && user);
  }

  function requireAuthForEnrollment() {
    if (isAuthenticated()) {
      return true;
    }

    const shouldLogin = window.confirm(
      'Чтобы подать заявку на курс, сначала нужно авторизоваться.\n\nПерейти к входу сейчас?'
    );

    if (shouldLogin) {
      if (typeof window.startLogin === 'function') {
        window.startLogin();
      } else {
        alert('Не удалось автоматически открыть авторизацию. Нажмите кнопку "Войти" в правом верхнем углу.');
      }
    }

    return false;
  }

  window.showEnrollForm = function () {
    window.showForm(`
      <h2>Создать заявку на курс</h2>
      <p class="small-hint">
        Публичная регистрация теперь всегда создаётся со статусом <strong>pending</strong>.
        Поле status с фронта больше не используется.
      </p>
      <form onsubmit="event.preventDefault(); enrollStudent();">
        <div class="form-row">
          <div class="form-group">
            <label>ID студента *</label>
            <input type="number" id="enroll-student" required>
          </div>
          <div class="form-group">
            <label>ID слота (slot_id / preferred_slot_id)</label>
            <input type="number" id="enroll-slot" placeholder="например: 12">
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>ID курса</label>
            <input type="number" id="enroll-course" placeholder="если без слота">
          </div>
          <div class="form-group">
            <label>ID категории</label>
            <input type="number" id="enroll-category">
          </div>
          <div class="form-group">
            <label>ID группы</label>
            <input type="number" id="enroll-group">
          </div>
          <div class="form-group">
            <label>ID блока</label>
            <input type="number" id="enroll-block">
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>Уровень (1-10)</label>
            <input type="number" id="enroll-level" min="1" max="10">
          </div>
          <div class="form-group" style="flex:2;">
            <label>Комментарий</label>
            <input type="text" id="enroll-comment" placeholder="например: есть базовый опыт Python">
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="post-btn">Отправить заявку</button>
          <button type="button" onclick="hideForms()">Отмена</button>
        </div>
      </form>
    `);
  };

  window.enrollStudent = function () {
    if (!requireAuthForEnrollment()) {
      return;
    }

    const studentValue = document.getElementById('enroll-student')?.value;
    if (!studentValue) {
      alert('Укажи ID студента.');
      return;
    }

    const data = {
      student_id: parseInt(studentValue, 10),
      comment: document.getElementById('enroll-comment').value || undefined
    };

    const slotValue = document.getElementById('enroll-slot').value;
    const courseValue = document.getElementById('enroll-course').value;
    const categoryValue = document.getElementById('enroll-category').value;
    const groupValue = document.getElementById('enroll-group').value;
    const blockValue = document.getElementById('enroll-block').value;
    const levelValue = document.getElementById('enroll-level').value;

    if (slotValue) data.preferred_slot_id = parseInt(slotValue, 10);
    if (courseValue) data.course_id = parseInt(courseValue, 10);
    if (categoryValue) data.category_id = parseInt(categoryValue, 10);
    if (groupValue) data.group_id = parseInt(groupValue, 10);
    if (blockValue) data.block_id = parseInt(blockValue, 10);
    if (levelValue) data.level = parseInt(levelValue, 10);

    window.makeRequest('POST', '/registration/enroll', data);
    window.hideForms();
  };

  window.getFilteredSlots = function () {
    const courseId = prompt('ID курса (оставьте пустым, чтобы пропустить):');
    const classroom = prompt('Аудитория (оставьте пустым, чтобы пропустить):');
    const day = prompt('День недели 1-7 (оставьте пустым, чтобы пропустить):');
    const year = prompt('Учебный год (например 2026-2027) (оставьте пустым, чтобы пропустить):');

    let url = '/registration/filter_slots?';
    const params = [];
    if (courseId) params.push(`course_id=${courseId}`);
    if (classroom) params.push(`classroom=${encodeURIComponent(classroom)}`);
    if (day) params.push(`day=${day}`);
    if (year) params.push(`academic_year=${encodeURIComponent(year)}`);

    window.makeRequest('GET', url + params.join('&'));
  };

  window.promptCompleteRegistration = function () {
    const regId = window.promptId('Введите ID регистрации:');
    if (regId) window.makeRequest('POST', `/registration/complete/${regId}`);
  };

  window.promptCompleteCourse = function () {
    const regId = window.promptId('Введите ID регистрации:');
    if (regId) window.makeRequest('POST', `/registration/complete/${regId}`);
  };
})();