(function () {
  const DAY_NAMES = {
    1: 'Понедельник',
    2: 'Вторник',
    3: 'Среда',
    4: 'Четверг',
    5: 'Пятница',
    6: 'Суббота',
    7: 'Воскресенье'
  };

  const ENTITY_META = {
    courses: { title: 'Курс', endpoint: (id) => `/search/details/courses/${id}` },
    teachers: { title: 'Преподаватель', endpoint: (id) => `/search/details/teachers/${id}` },
    classrooms: { title: 'Аудитория', endpoint: (id) => `/search/details/classrooms/${id}` },
    students: { title: 'Студент', endpoint: (id) => `/search/details/students/${id}` },
    'course-groups': { title: 'Группа', endpoint: (id) => `/search/details/course-groups/${id}` },
    'schedule-slots': { title: 'Слот', endpoint: (id) => `/search/details/schedule-slots/${id}` }
  };

  let lastPreviewResult = null;
  let lastBucketResult = null;

  function esc(v) {
    return window.escapeHtml ? window.escapeHtml(v) : String(v ?? '');
  }

  function val(v) {
    return window.formatValue ? window.formatValue(v) : (v ?? '—');
  }

  function dayName(day) {
    return DAY_NAMES[day] || `День ${day}`;
  }



  function getControls() {
    return {
      year: document.getElementById('sg-academic-year'),
      minSize: document.getElementById('sg-min-group-size'),
      status: document.getElementById('sg-status'),
      summary: document.getElementById('sg-summary'),
      warnings: document.getElementById('sg-warnings'),
      courseStats: document.getElementById('sg-course-stats'),
      groups: document.getElementById('sg-groups'),
      unassigned: document.getElementById('sg-unassigned'),
      buckets: document.getElementById('sg-buckets'),
      detail: document.getElementById('sg-detail'),
      response: document.getElementById('response-section')
    };
  }

  function setStatus(text, kind = 'muted') {
    const el = getControls().status;
    if (!el) return;

    const className =
      kind === 'error' ? 'status-chip status-bad' :
      kind === 'success' ? 'status-chip status-ok' :
      '';

    el.innerHTML = className ? `<span class="${className}">${esc(text)}</span>` : esc(text);
  }

  function showEmpty(id, text) {
    const node = document.getElementById(id);
    if (node) {
      node.innerHTML = `<div class="empty-box">${esc(text)}</div>`;
    }
  }

  function renderSummary(summary) {
    const box = getControls().summary;
    if (!box) return;

    if (!summary) {
      box.innerHTML = `<div class="empty-box">Результат ещё не рассчитан.</div>`;
      return;
    }

    box.innerHTML = `
      <div class="summary-grid">
        <div class="summary-card primary">
          <div class="summary-label">Заявок в расчёте</div>
          <div class="summary-value">${esc(summary.total_registrations_in_scope || 0)}</div>
        </div>
        <div class="summary-card success">
          <div class="summary-label">Распределено</div>
          <div class="summary-value">${esc(summary.assigned || 0)}</div>
        </div>
        <div class="summary-card warning">
          <div class="summary-label">Нераспределено</div>
          <div class="summary-value">${esc(summary.unassigned || 0)}</div>
        </div>
        <div class="summary-card info">
          <div class="summary-label">Групп к созданию</div>
          <div class="summary-value">${esc(summary.groups_to_create || 0)}</div>
        </div>
      </div>
    `;
  }

  function renderWarnings(warnings) {
    const box = getControls().warnings;
    if (!box) return;

    if (!warnings || !warnings.length) {
      box.innerHTML = `<div class="empty-box">Предупреждений нет.</div>`;
      return;
    }

    box.innerHTML = warnings.map((warning) => `
      <div class="warning-card">
        <div class="group-card-title">${esc(warning.course_name || warning.type || 'Предупреждение')}</div>
        <div class="group-card-meta">${esc(warning.message || '')}</div>
        <div class="tag-row">
          ${warning.slot_id ? `<span class="tag-chip">slot_id: ${esc(warning.slot_id)}</span>` : ''}
          ${warning.assigned_count !== undefined ? `<span class="tag-chip">Студентов: ${esc(warning.assigned_count)}</span>` : ''}
          ${warning.min_group_size !== undefined ? `<span class="tag-chip">Мин. размер: ${esc(warning.min_group_size)}</span>` : ''}
        </div>
      </div>
    `).join('');
  }

  function renderCourseStats(stats) {
    const box = getControls().courseStats;
    if (!box) return;

    if (!stats || !stats.length) {
      box.innerHTML = `<div class="empty-box">Статистика по курсам пока не построена.</div>`;
      return;
    }

    box.innerHTML = `
      <div class="course-stat-grid">
        ${stats.map((row) => `
          <div class="stat-card">
            <div class="group-card-title">Course #${esc(row.course_id)}</div>
            <div class="group-card-meta">Распределено: ${esc(row.assigned || 0)}</div>
            <div class="group-card-meta">Нераспределено: ${esc(row.unassigned || 0)}</div>
          </div>
        `).join('')}
      </div>
    `;
  }

  function buildAssignmentRows(preview) {
    if (!preview.registration_ids || !preview.registration_ids.length || !lastPreviewResult?.assigned_registrations) {
      return `<div class="empty-box">Назначений пока нет.</div>`;
    }

    const registrations = lastPreviewResult.assigned_registrations.filter((row) =>
      preview.registration_ids.includes(row.registration_id)
    );

    if (!registrations.length) {
      return `<div class="empty-box">Назначения для этой карточки не найдены.</div>`;
    }

    return `
      <div class="assignment-list">
        ${registrations.map((row) => `
          <div class="assignment-row">
            <div class="group-card-title">${esc(row.student_name)}</div>
            <div class="assignment-meta">Уровень: ${esc(row.level)}</div>
            <div class="assignment-meta">Причина: ${esc(row.assignment_reason)}</div>
            <div class="link-row">
              <button class="ghost-btn link-chip" data-entity="students" data-id="${esc(row.student_id)}">Студент #${esc(row.student_id)}</button>
              <span class="tag-chip">registration_id: ${esc(row.registration_id)}</span>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  function openSyntheticGroupDetail(preview) {
    const box = getControls().detail;
    if (!box) return;

    box.innerHTML = `
      <div class="detail-kicker">Предпросмотр группы</div>
      <div class="detail-title">${esc(preview.group_name_preview || preview.course_name || 'Группа')}</div>
      <div class="detail-id">slot_id: ${esc(preview.slot_id)}</div>

      <div class="entity-grid">
        <div class="entity-field">
          <div class="entity-field-label">Курс</div>
          <div class="entity-field-value">${esc(preview.course_name || '—')}</div>
        </div>
        <div class="entity-field">
          <div class="entity-field-label">Преподаватель</div>
          <div class="entity-field-value">${esc(preview.teacher_name || '—')}</div>
        </div>
        <div class="entity-field">
          <div class="entity-field-label">Время</div>
          <div class="entity-field-value">${esc(dayName(preview.day_of_week))}, ${esc(preview.start_time)}–${esc(preview.end_time)}</div>
        </div>
        <div class="entity-field">
          <div class="entity-field-label">Аудитория</div>
          <div class="entity-field-value">${esc(preview.classroom_name || '—')}</div>
        </div>
        <div class="entity-field">
          <div class="entity-field-label">Заполнено</div>
          <div class="entity-field-value">${esc(preview.assigned_count)} / ${esc(preview.capacity)}</div>
        </div>
        <div class="entity-field">
          <div class="entity-field-label">Уровни</div>
          <div class="entity-field-value">${esc(preview.min_level_in_group)} – ${esc(preview.max_level_in_group)}</div>
        </div>
      </div>

      <div class="detail-section">
        <div class="detail-section-title">Связанные сущности</div>
        <div class="link-row">
          ${preview.course_id ? `<button class="ghost-btn link-chip" data-entity="courses" data-id="${esc(preview.course_id)}">Курс</button>` : ''}
          ${preview.teacher_id ? `<button class="ghost-btn link-chip" data-entity="teachers" data-id="${esc(preview.teacher_id)}">Преподаватель</button>` : ''}
          ${preview.classroom_id ? `<button class="ghost-btn link-chip" data-entity="classrooms" data-id="${esc(preview.classroom_id)}">Аудитория</button>` : ''}
        </div>
      </div>

      <div class="detail-section">
        <div class="detail-section-title">Назначенные дети</div>
        ${buildAssignmentRows(preview)}
      </div>
    `;

    bindEntityLinks(box);
  }

  function renderGroupCards(groups) {
    const box = getControls().groups;
    if (!box) return;

    if (!groups || !groups.length) {
      box.innerHTML = `<div class="empty-box">Группы пока не рассчитаны.</div>`;
      return;
    }

    box.innerHTML = `
      <div class="group-card-grid">
        ${groups.map((group, index) => `
          <div class="group-card clickable" data-preview-index="${index}">
            <div class="group-card-head">
              <div>
                <div class="group-card-title">${esc(group.group_name_preview || group.course_name || 'Группа')}</div>
                <div class="group-card-meta">${esc(dayName(group.day_of_week))} · ${esc(group.start_time)}–${esc(group.end_time)}</div>
                <div class="group-card-meta">${esc(group.classroom_name || 'Без аудитории')} · ${esc(group.teacher_name || 'Без преподавателя')}</div>
              </div>
              ${group.underfilled ? `<span class="queue-badge rigid">Маленькая</span>` : `<span class="state-badge">Ок</span>`}
            </div>

            <div class="tag-row">
              <span class="tag-chip">Заполнено: ${esc(group.assigned_count)}/${esc(group.capacity)}</span>
              <span class="tag-chip">Свободно: ${esc(group.remaining_capacity)}</span>
              <span class="tag-chip">Уровни: ${esc(group.min_level_in_group)}–${esc(group.max_level_in_group)}</span>
            </div>

            <div class="link-row">
              ${group.course_id ? `<button class="ghost-btn link-chip" data-entity="courses" data-id="${esc(group.course_id)}">Курс</button>` : ''}
              ${group.teacher_id ? `<button class="ghost-btn link-chip" data-entity="teachers" data-id="${esc(group.teacher_id)}">Преподаватель</button>` : ''}
              ${group.classroom_id ? `<button class="ghost-btn link-chip" data-entity="classrooms" data-id="${esc(group.classroom_id)}">Аудитория</button>` : ''}
            </div>
          </div>
        `).join('')}
      </div>
    `;

    box.querySelectorAll('[data-preview-index]').forEach((node) => {
      node.addEventListener('click', function (event) {
        if (event.target.closest('[data-entity]')) return;
        const idx = parseInt(node.getAttribute('data-preview-index'), 10);
        const preview = groups[idx];
        if (preview) openSyntheticGroupDetail(preview);
      });
    });

    bindEntityLinks(box);
  }

  function renderUnassigned(rows) {
    const box = getControls().unassigned;
    if (!box) return;

    if (!rows || !rows.length) {
      box.innerHTML = `<div class="empty-box">Все дети распределены.</div>`;
      return;
    }

    box.innerHTML = `
      <div class="unassigned-grid">
        ${rows.map((row) => `
          <div class="unassigned-card">
            <div class="group-card-title">${esc(row.student_name)}</div>
            <div class="group-card-meta">${esc(row.course_name || `Course #${row.course_id}`)}</div>
            <div class="group-card-meta">Уровень: ${esc(row.level)}</div>
            <div class="group-card-meta">${esc(row.reason)}</div>
            <div class="link-row">
              <button class="ghost-btn link-chip" data-entity="students" data-id="${esc(row.student_id)}">Студент</button>
              ${row.course_id ? `<button class="ghost-btn link-chip" data-entity="courses" data-id="${esc(row.course_id)}">Курс</button>` : ''}
            </div>
          </div>
        `).join('')}
      </div>
    `;

    bindEntityLinks(box);
  }

  function openBucketDetail(bucket) {
    const box = getControls().detail;
    if (!box) return;

    box.innerHTML = `
      <div class="detail-kicker">Bucket</div>
      <div class="detail-title">${esc(bucket.course_name || `Course #${bucket.course_id}`)}</div>
      <div class="detail-id">${esc(dayName(bucket.day_of_week))} · ${esc(bucket.start_time)}–${esc(bucket.end_time)}</div>

      <div class="entity-grid">
        <div class="entity-field">
          <div class="entity-field-label">Rigid</div>
          <div class="entity-field-value">${esc(bucket.rigid_count || 0)}</div>
        </div>
        <div class="entity-field">
          <div class="entity-field-label">Спрос</div>
          <div class="entity-field-value">${esc(bucket.total_demand || 0)}</div>
        </div>
        <div class="entity-field">
          <div class="entity-field-label">Спрос / преподаватель</div>
          <div class="entity-field-value">${esc(bucket.demand_per_teacher || 0)}</div>
        </div>
      </div>

      <div class="detail-section">
        <div class="detail-section-title">Назначены в этом bucket</div>
        ${
          bucket.assigned && bucket.assigned.length
            ? `<div class="assignment-list">
                ${bucket.assigned.map((row) => `
                  <div class="assignment-row">
                    <div class="group-card-title">registration #${esc(row.registration_id)}</div>
                    <div class="assignment-meta">student_id: ${esc(row.student_id)}</div>
                    <div class="assignment-meta">slot_id: ${esc(row.slot_id)}</div>
                    <div class="assignment-meta">Очередь: ${esc(row.queue)}</div>
                    <div class="link-row">
                      <button class="ghost-btn link-chip" data-entity="students" data-id="${esc(row.student_id)}">Студент</button>
                    </div>
                  </div>
                `).join('')}
              </div>`
            : `<div class="empty-box">Никого не назначили.</div>`
        }
      </div>

      <div class="detail-section">
        <div class="detail-section-title">Отклонены внутри bucket</div>
        ${
          bucket.rejected_in_bucket && bucket.rejected_in_bucket.length
            ? `<div class="assignment-list">
                ${bucket.rejected_in_bucket.map((row) => `
                  <div class="assignment-row">
                    <div class="group-card-title">registration #${esc(row.registration_id)}</div>
                    <div class="assignment-meta">student_id: ${esc(row.student_id)}</div>
                    <div class="assignment-meta">${esc(row.reason)}</div>
                    <div class="assignment-meta">Очередь: ${esc(row.queue)}</div>
                    <div class="link-row">
                      <button class="ghost-btn link-chip" data-entity="students" data-id="${esc(row.student_id)}">Студент</button>
                    </div>
                  </div>
                `).join('')}
              </div>`
            : `<div class="empty-box">Отклонённых нет.</div>`
        }
      </div>
    `;

    bindEntityLinks(box);
  }

  function renderBuckets(rows) {
    const box = getControls().buckets;
    if (!box) return;

    if (!rows || !rows.length) {
      box.innerHTML = `<div class="empty-box">Bucket’ы пока не загружены.</div>`;
      return;
    }

    box.innerHTML = `
      <div class="bucket-grid">
        ${rows.map((bucket, index) => `
          <div class="bucket-card clickable" data-bucket-index="${index}">
            <div class="bucket-title">${esc(bucket.course_name || `Course #${bucket.course_id}`)}</div>
            <div class="bucket-meta">${esc(dayName(bucket.day_of_week))} · ${esc(bucket.start_time)}–${esc(bucket.end_time)}</div>
            <div class="tag-row">
              <span class="tag-chip">Rigid: ${esc(bucket.rigid_count || 0)}</span>
              <span class="tag-chip">Спрос: ${esc(bucket.total_demand || 0)}</span>
              <span class="tag-chip">/ преп.: ${esc(bucket.demand_per_teacher || 0)}</span>
            </div>
          </div>
        `).join('')}
      </div>
    `;

    box.querySelectorAll('[data-bucket-index]').forEach((node) => {
      node.addEventListener('click', function () {
        const idx = parseInt(node.getAttribute('data-bucket-index'), 10);
        const bucket = rows[idx];
        if (bucket) openBucketDetail(bucket);
      });
    });
  }

  function renderGenerationResult(result) {
    lastPreviewResult = result;
    renderSummary(result.summary);
    renderWarnings(result.warnings);
    renderCourseStats(result.course_stats);
    renderGroupCards(result.group_previews);
    renderUnassigned(result.unassigned_registrations);
    renderBuckets(result.bucket_report);
  }

  function renderDebugBuckets(result) {
    lastBucketResult = result;
    renderBuckets(result.buckets || []);
  }

  function makePrimaryDetail() {
    const box = getControls().detail;
    if (!box) return;

    box.innerHTML = `
      <div class="detail-kicker">Рабочая область</div>
      <div class="detail-title">Генерация расписания</div>
      <div class="detail-id">Выбери группу, bucket или связанную сущность слева.</div>
      <div class="detail-section">
        <div class="detail-section-title">Что можно открыть отсюда</div>
        <div class="mini-grid">
          <div class="mini-card">
            <div class="mini-title">Карточка preview-группы</div>
            <div class="mini-subtitle">Увидишь состав, уровень, слот, аудиторию и быстрые переходы.</div>
          </div>
          <div class="mini-card">
            <div class="mini-title">Bucket приоритизации</div>
            <div class="mini-subtitle">Покажет спрос, rigid/alternative детей и причины отклонений.</div>
          </div>
          <div class="mini-card">
            <div class="mini-title">Сущность из базы</div>
            <div class="mini-subtitle">Курс, преподаватель, аудитория или студент откроются справа как карточка.</div>
          </div>
        </div>
      </div>
    `;
  }

  function collectLinks(value, path = [], links = []) {
    if (value === null || value === undefined) return links;

    if (Array.isArray(value)) {
      value.forEach((item, index) => collectLinks(item, path.concat(index), links));
      return links;
    }

    if (typeof value === 'object') {
      if (value.id && typeof value.id !== 'object') {
        const last = path[path.length - 1];
        const field = typeof last === 'string' ? last : null;
        let entity = null;

        if (field === 'course') entity = 'courses';
        else if (field === 'teacher' || field === 'lead_teacher') entity = 'teachers';
        else if (field === 'classroom') entity = 'classrooms';
        else if (field === 'student') entity = 'students';
        else if (field === 'group') entity = 'course-groups';
        else if (field === 'schedule_slot') entity = 'schedule-slots';

        if (entity) {
          links.push({
            entity,
            id: value.id,
            label: value.full_name || value.label || value.name || `${entity} #${value.id}`
          });
        }
      }

      Object.entries(value).forEach(([key, nested]) => collectLinks(nested, path.concat(key), links));
    }

    return links;
  }

  function renderObjectDetails(data) {
    const links = collectLinks(data);
    const fields = Object.entries(data || {})
      .filter(([_, value]) => typeof value !== 'object' || value === null)
      .slice(0, 12);

    return `
      <div class="entity-grid">
        ${fields.map(([key, value]) => `
          <div class="entity-field">
            <div class="entity-field-label">${esc(key)}</div>
            <div class="entity-field-value">${esc(val(value))}</div>
          </div>
        `).join('')}
      </div>

      ${
        links.length
          ? `<div class="detail-section">
              <div class="detail-section-title">Связанные сущности</div>
              <div class="link-row">
                ${links.map((link) => `
                  <button class="ghost-btn link-chip" data-entity="${esc(link.entity)}" data-id="${esc(link.id)}">
                    ${esc(link.label)}
                  </button>
                `).join('')}
              </div>
            </div>`
          : ''
      }

      <div class="detail-section">
        <div class="detail-section-title">Технический JSON</div>
        <div class="json-display">${window.syntaxHighlight ? window.syntaxHighlight(data) : esc(JSON.stringify(data, null, 2))}</div>
      </div>
    `;
  }

  async function openEntity(entity, id, label = '') {
    const meta = ENTITY_META[entity];
    const box = getControls().detail;
    if (!meta || !box) return;

    box.innerHTML = `<div class="loading-box">Загрузка ${esc(meta.title.toLowerCase())}...</div>`;
    const result = await window.apiGet(meta.endpoint(id).replace(window.API_BASE, ''));
    if (!result.ok) {
      box.innerHTML = `<div class="empty-box">Не удалось загрузить сущность. HTTP ${esc(result.status)}</div>`;
      return;
    }

    box.innerHTML = `
      <div class="detail-kicker">${esc(meta.title)}</div>
      <div class="detail-title">${esc(label || result.data?.name || result.data?.full_name || result.data?.label || `${meta.title} #${id}`)}</div>
      <div class="detail-id">ID: ${esc(id)}</div>
      ${renderObjectDetails(result.data)}
    `;

    bindEntityLinks(box);
  }

  function bindEntityLinks(root = document) {
    root.querySelectorAll('[data-entity][data-id]').forEach((node) => {
      node.addEventListener('click', function (event) {
        event.stopPropagation();
        const entity = node.getAttribute('data-entity');
        const id = node.getAttribute('data-id');
        const label = node.textContent.trim();
        openEntity(entity, id, label);
      });
    });
  }

  async function previewSchedule() {
    const { year, minSize } = getControls();
    if (!year?.value) {
      setStatus('Учебный год не определён', 'error');
      return;
    }

    setStatus('Считаю preview...');
    const result = await window.apiGet('/schedule-generation/preview', {
      academic_year: year.value,
      min_group_size: minSize.value || undefined
    });

    if (!result.ok) {
      setStatus(result.data?.error || `Ошибка HTTP ${result.status}`, 'error');
      return;
    }

    renderGenerationResult(result.data);
    setStatus('Preview готов', 'success');
  }

  async function generateSchedule() {
    const { year, minSize } = getControls();
    if (!year?.value) {
      setStatus('Учебный год не определён', 'error');
      return;
    }

    if (!window.confirm('Сгенерировать группы и записать результат в базу?')) return;

    setStatus('Записываю результат в базу...');
    const result = await window.apiPost('/schedule-generation/generate', {
      academic_year: year.value,
      min_group_size: minSize.value ? parseInt(minSize.value, 10) : undefined
    });

    if (!result.ok) {
      setStatus(result.data?.error || `Ошибка HTTP ${result.status}`, 'error');
      return;
    }

    renderGenerationResult(result.data);
    setStatus('Генерация завершена и сохранена', 'success');
  }

  async function loadBuckets() {
    const { year } = getControls();
    if (!year?.value) {
      setStatus('Учебный год не определён', 'error');
      return;
    }

    setStatus('Загружаю bucket-отладку...');
    const result = await window.apiGet('/schedule-generation/buckets', {
      academic_year: year.value
    });

    if (!result.ok) {
      setStatus(result.data?.error || `Ошибка HTTP ${result.status}`, 'error');
      return;
    }

    renderDebugBuckets(result.data);
    setStatus('Bucket’ы загружены', 'success');
  }

  function clearResults() {
    lastPreviewResult = null;
    lastBucketResult = null;
    renderSummary(null);
    renderWarnings([]);
    renderCourseStats([]);
    showEmpty('sg-groups', 'Группы пока не рассчитаны.');
    showEmpty('sg-unassigned', 'Здесь будут дети, которых не удалось распределить.');
    showEmpty('sg-buckets', 'Bucket’ы пока не загружены.');
    makePrimaryDetail();
    setStatus('Результаты очищены');
  }


  async function initDefaults() {
    await loadAcademicYear();

    const minSize = document.getElementById('sg-min-group-size');
    if (minSize && !minSize.value) {
      minSize.value = '4';
    }

    clearResults();
  }

  async function loadAcademicYear() {
    const yearInput = document.getElementById('sg-academic-year');
    if (!yearInput) return;

    try {
      const result = await window.apiGet('/auth/academic-year');
      if (result.ok && result.data?.academic_year) {
        yearInput.value = result.data.academic_year;
      } else {
        yearInput.value = '';
      }
    } catch (e) {
      yearInput.value = '';
    }

    yearInput.readOnly = true;
    yearInput.setAttribute('readonly', 'readonly');
    yearInput.title = '';
    yearInput.style.backgroundColor = '#f3f4f6';
    yearInput.style.cursor = 'default';
  }

  document.addEventListener('DOMContentLoaded', async function () {
    await initDefaults();

    document.getElementById('sg-preview-btn')?.addEventListener('click', previewSchedule);
    document.getElementById('sg-generate-btn')?.addEventListener('click', generateSchedule);
    document.getElementById('sg-buckets-btn')?.addEventListener('click', loadBuckets);
    document.getElementById('sg-clear-btn')?.addEventListener('click', clearResults);
  });
})();