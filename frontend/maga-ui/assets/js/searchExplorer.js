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

  const SEARCH_ENTITIES = {
    'courses': {
      title: 'Курсы',
      hint: 'Поиск по названию курса и направлению',
      placeholder: 'Например: Робототехника',
      searchEntity: 'courses',
      detailsEndpoint: (id) => `/courses/${id}`
    },
    'course-categories': {
      title: 'Направления',
      hint: 'Поиск по названию направления и уровню обучения',
      placeholder: 'Например: Программирование',
      searchEntity: 'course-categories',
      detailsEndpoint: (id) => `/course-categories/${id}`
    },
    'informatics-blocks': {
      title: 'Блоки информатики',
      hint: 'Поиск по названию блока и курсу',
      placeholder: 'Например: Python',
      searchEntity: 'informatics-blocks',
      detailsEndpoint: (id) => `/informatics-blocks/${id}`
    },
    'students': {
      title: 'Студенты',
      hint: 'Поиск по ФИО, школе и классу',
      placeholder: 'Например: Иванов 7А',
      searchEntity: 'students',
      detailsEndpoint: (id) => `/students/${id}`
    },
    'teachers': {
      title: 'Преподаватели',
      hint: 'Поиск по ФИО и email',
      placeholder: 'Например: Петров',
      searchEntity: 'teachers',
      detailsEndpoint: (id) => `/teachers/${id}`
    },
    'assistants': {
      title: 'Ассистенты',
      hint: 'Поиск по ФИО, телефону и email',
      placeholder: 'Например: Сидоров',
      searchEntity: 'assistants',
      detailsEndpoint: (id) => `/assistants/${id}`
    },
    'classrooms': {
      title: 'Аудитории',
      hint: 'Поиск по названию аудитории',
      placeholder: 'Например: 101',
      searchEntity: 'classrooms',
      detailsEndpoint: (id) => `/classrooms/${id}`
    },
    'schedule-slots': {
      title: 'Слоты расписания',
      hint: 'Поиск по дню, времени, группе и аудитории',
      placeholder: 'Например: понедельник 15:00',
      searchEntity: 'schedule-slots',
      detailsEndpoint: (id) => `/schedule/${id}`
    },
    'assistant-substitutions': {
      title: 'Подмены ассистентов',
      hint: 'Поиск по дате и группе',
      placeholder: 'Например: 2026-09-12',
      searchEntity: 'assistant-substitutions',
      detailsEndpoint: (id) => `/assistant-substitutions/${id}`
    }
  };

  const PUBLIC_DETAIL_ENTITIES = new Set(['courses', 'course-categories', 'informatics-blocks']);
  const MANAGER_ONLY_ENTITIES = new Set([
    'students',
    'teachers',
    'assistants',
    'classrooms',
    'schedule-slots',
    'assistant-substitutions'
  ]);

  function hasRole(...roles) {
    const currentRoles = window.currentUserRoles || [];
    return roles.some((role) => currentRoles.includes(role));
  }

  function canUseManagerSearch() {
    return hasRole('manager', 'admin');
  }

  function canUseGroupStudents() {
    return hasRole('teacher', 'assistant', 'manager', 'admin');
  }

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function formatValue(value) {
    if (value === null || value === undefined || value === '') return '—';
    if (typeof value === 'boolean') return value ? 'Да' : 'Нет';
    return String(value);
  }

  function dayName(day) {
    return DAY_NAMES[day] || `День ${day}`;
  }

  function debounce(fn, wait = 250) {
    let timeout = null;
    return function (...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => fn.apply(this, args), wait);
    };
  }

  function setSearchStatus(text) {
    const el = document.getElementById('search-explorer-status');
    if (el) el.textContent = text || '';
  }

  function renderEmpty(text) {
    return `<div class="empty-box">${escapeHtml(text)}</div>`;
  }

  function renderTags(items) {
    if (!items || !items.length) return '—';
    return items.map((item) => `<span class="tag-chip">${escapeHtml(item)}</span>`).join(' ');
  }

  function renderField(label, value) {
    return `
      <div class="entity-field">
        <div class="entity-field-label">${escapeHtml(label)}</div>
        <div class="entity-field-value">${escapeHtml(formatValue(value))}</div>
      </div>
    `;
  }

  function renderBool(value) {
    return value ? 'Да' : 'Нет';
  }

  async function fetchJson(base, endpoint, params = {}) {
    const url = new URL(`${base}${endpoint}`, window.location.origin);
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, String(v));
    });

    const headers = {};
    const token = (typeof window.getAccessToken === 'function' ? window.getAccessToken() : (localStorage.getItem('access_token') || localStorage.getItem('token')));
    if (token) headers.Authorization = `Bearer ${token}`;

    const startedAt = Date.now();
    try {
      const response = await fetch(url.toString(), { headers });
      const text = await response.text();

      let data = text;
      try {
        data = text ? JSON.parse(text) : null;
      } catch (_) {}

      return {
        ok: response.ok,
        status: response.status,
        data,
        responseTime: Date.now() - startedAt
      };
    } catch (error) {
      return {
        ok: false,
        status: 0,
        data: { error: error.message },
        responseTime: Date.now() - startedAt
      };
    }
  }

  async function putJson(base, endpoint, payload) {
    return sendJson('PUT', base, endpoint, payload);
  }

  async function postJson(base, endpoint, payload) {
    return sendJson('POST', base, endpoint, payload);
  }

  async function deleteJson(base, endpoint) {
    return sendJson('DELETE', base, endpoint);
  }

  async function sendJson(method, base, endpoint, payload) {
    const url = `${base}${endpoint}`;
    const headers = { 'Content-Type': 'application/json' };
    const token = (typeof window.getAccessToken === 'function' ? window.getAccessToken() : (localStorage.getItem('access_token') || localStorage.getItem('token')));
    if (token) headers.Authorization = `Bearer ${token}`;

    const startedAt = Date.now();
    try {
      const response = await fetch(url, {
        method,
        headers,
        body: payload ? JSON.stringify(payload) : undefined
      });

      const text = await response.text();
      let data = text;
      try {
        data = text ? JSON.parse(text) : null;
      } catch (_) {}

      return {
        ok: response.ok,
        status: response.status,
        data,
        responseTime: Date.now() - startedAt
      };
    } catch (error) {
      return {
        ok: false,
        status: 0,
        data: { error: error.message },
        responseTime: Date.now() - startedAt
      };
    }
  }

  function renderMiniCard(title, subtitle, meta = '', nav = null) {
    const buttonAttrs = nav
      ? `data-nav-entity="${escapeHtml(nav.entity)}" data-nav-id="${escapeHtml(nav.id)}"`
      : '';

    return `
      <button type="button" class="mini-card mini-card-button" ${buttonAttrs}>
        <div class="mini-title">${escapeHtml(title || '—')}</div>
        <div class="mini-subtitle">${escapeHtml(subtitle || '—')}</div>
        ${meta ? `<div class="mini-meta">${escapeHtml(meta)}</div>` : ''}
      </button>
    `;
  }

  function renderMiniGrid(items, renderer, emptyText) {
    if (!items || !items.length) return renderEmpty(emptyText);
    return `<div class="mini-grid">${items.map(renderer).join('')}</div>`;
  }

  function renderStudentsRegistrationGrid(rows) {
    if (!rows || !rows.length) return renderEmpty('Студенты не найдены.');

    return `
      <div class="mini-grid">
        ${rows.map((row) => {
          const student = row.student || {};
          return renderMiniCard(
            student.full_name || `${student.lastname || ''} ${student.firstname || ''}`.trim(),
            `Статус: ${row.status_ru || row.status || '—'}`,
            `Уровень: ${formatValue(row.level)}`,
            student.id ? { entity: 'students', id: student.id } : null
          );
        }).join('')}
      </div>
    `;
  }

  function renderScheduleGrid(slots) {
    if (!slots || !slots.length) return renderEmpty('Слоты не найдены.');

    return `
      <div class="mini-grid">
        ${slots.map((slot) => renderMiniCard(
          `${dayName(slot.day_of_week)} • ${slot.start_time || '—'}-${slot.end_time || '—'}`,
          slot.group ? (slot.group.label || slot.group.name || 'Группа') : (slot.group_name || 'Группа'),
          slot.classroom ? (slot.classroom.name || slot.classroom) : (slot.classroom || 'Без аудитории'),
          slot.id ? { entity: 'schedule-slots', id: slot.id } : null
        )).join('')}
      </div>
    `;
  }

  function renderParents(parents) {
    if (!parents || !parents.length) return renderEmpty('Родители не найдены.');
    return `
      <div class="mini-grid">
        ${parents.map((p) => renderMiniCard(
          p.full_name || `${p.lastname || ''} ${p.firstname || ''}`.trim(),
          p.email || p.phone_number || '—',
          p.address || ''
        )).join('')}
      </div>
    `;
  }

  function renderPreferences(prefs) {
    if (!prefs || !prefs.length) return renderEmpty('Предпочтений нет.');
    return `
      <div class="mini-grid">
        ${prefs.map((pref) => renderMiniCard(
          `Предпочтение #${pref.id}`,
          pref.preference_text || '—',
          `Обработано: ${pref.processed ? 'Да' : 'Нет'}`
        )).join('')}
      </div>
    `;
  }

  function renderRegistrations(regs) {
    if (!regs || !regs.length) return renderEmpty('Регистраций нет.');
    return `
      <div class="mini-grid">
        ${regs.map((reg) => renderMiniCard(
          reg.course ? (reg.course.name || 'Курс') : 'Курс',
          reg.status_ru || reg.status || '—',
          reg.group ? (reg.group.label || reg.group.name || '') : ''
        )).join('')}
      </div>
    `;
  }

  function renderSection(title, bodyHtml) {
    return `
      <div class="detail-section">
        <div class="detail-section-title">${escapeHtml(title)}</div>
        ${bodyHtml}
      </div>
    `;
  }

  function renderEntityActions(entity, id) {
    if (!canUseManagerSearch()) return '';
    return `
      <div class="entity-actions">
        <button type="button" class="put-btn" data-entity-action="edit" data-entity="${escapeHtml(entity)}" data-id="${escapeHtml(id)}">Редактировать</button>
        <button type="button" class="delete-btn" data-entity-action="delete" data-entity="${escapeHtml(entity)}" data-id="${escapeHtml(id)}">Удалить</button>
      </div>
    `;
  }

  function renderCard(meta, data) {
    if (!data || typeof data !== 'object' || Array.isArray(data)) {
      return renderEmpty('Не удалось построить карточку.');
    }

    const actions = renderEntityActions(meta.searchEntity, data.id);

    switch (meta.searchEntity) {
      case 'students':
        return `
          ${actions}
          <div class="entity-card-grid">
            ${renderField('Имя', data.firstname)}
            ${renderField('Фамилия', data.lastname)}
            ${renderField('Отчество', data.surname)}
            ${renderField('Дата рождения', data.birthday)}
            ${renderField('Телефон', data.phone_number)}
            ${renderField('Email', data.email)}
            ${renderField('Адрес', data.address)}
            ${renderField('Учебное заведение', data.educational_institution)}
            ${renderField('Группа/класс', data.group_name)}
            ${renderField('Тип обучения', data.education_type)}
            ${renderField('Зачислен в этом году', renderBool(data.enrolled_this_year))}
          </div>
          ${renderSection('Родители', renderParents(data.parents))}
          ${renderSection('Регистрации', renderRegistrations(data.registrations))}
          ${renderSection('Предпочтения', renderPreferences(data.preferences))}
        `;

      case 'teachers':
        return `
          ${actions}
          <div class="entity-card-grid">
            ${renderField('Имя', data.firstname)}
            ${renderField('Фамилия', data.lastname)}
            ${renderField('Отчество', data.surname)}
            ${renderField('Дата рождения', data.birthday)}
            ${renderField('Телефон', data.phone_number)}
            ${renderField('Email', data.email)}
          </div>
          ${renderSection(
            'Может вести курсы',
            renderMiniGrid(
              data.allowed_courses,
              (course) => renderMiniCard(
                course.name,
                course.category || 'Без направления',
                '',
                course.id ? { entity: 'courses', id: course.id } : null
              ),
              'Курсы не назначены.'
            )
          )}
          ${renderSection(
            'Ведёт группы',
            renderMiniGrid(
              data.lead_groups,
              (group) => renderMiniCard(
                group.label || group.name,
                group.schedule_slot ? `${dayName(group.schedule_slot.day_of_week)} • ${group.schedule_slot.start_time}-${group.schedule_slot.end_time}` : 'Слот не назначен',
                group.schedule_slot && group.schedule_slot.classroom ? `Аудитория: ${group.schedule_slot.classroom}` : '',
                group.id ? { entity: 'course-groups', id: group.id } : null
              ),
              'Группы не назначены.'
            )
          )}
        `;

      case 'assistants':
        return `
          ${actions}
          <div class="entity-card-grid">
            ${renderField('Имя', data.firstname)}
            ${renderField('Фамилия', data.lastname)}
            ${renderField('Отчество', data.surname)}
            ${renderField('Дата рождения', data.birthday)}
            ${renderField('Телефон', data.phone_number)}
            ${renderField('Email', data.email)}
          </div>
          ${renderSection(
            'Привязан к группам',
            renderMiniGrid(
              data.groups,
              (group) => renderMiniCard(
                group.label || group.name,
                group.schedule_slot ? `${dayName(group.schedule_slot.day_of_week)} • ${group.schedule_slot.start_time}-${group.schedule_slot.end_time}` : 'Слот не назначен',
                group.schedule_slot && group.schedule_slot.classroom ? `Аудитория: ${group.schedule_slot.classroom}` : '',
                group.id ? { entity: 'course-groups', id: group.id } : null
              ),
              'Группы не найдены.'
            )
          )}
        `;

      case 'courses':
        return `
          ${actions}
          <div class="entity-card-grid">
            ${renderField('Название', data.name)}
            ${renderField('Описание', data.description)}
            ${renderField('Направление', data.category ? data.category.name : null)}
            ${renderField('Макс. студентов', data.max_students)}
            ${renderField('По вместимости аудитории', renderBool(data.use_classroom_capacity))}
            ${renderField('Длительность, мин', data.duration_minutes)}
            ${renderField('Цена', data.price)}
            ${renderField('Активен', renderBool(data.is_active))}
          </div>
          ${renderSection(
            'Преподаватели курса',
            renderMiniGrid(
              data.allowed_teachers,
              (t) => renderMiniCard(
                t.full_name || `${t.lastname || ''} ${t.firstname || ''}`.trim(),
                t.email || t.phone_number || '—',
                '',
                t.id ? { entity: 'teachers', id: t.id } : null
              ),
              'Преподаватели не назначены.'
            )
          )}
          ${renderSection(
            'Группы курса',
            renderMiniGrid(
              data.groups,
              (g) => renderMiniCard(
                g.label || g.name,
                g.schedule_slot ? `${dayName(g.schedule_slot.day_of_week)} • ${g.schedule_slot.start_time}-${g.schedule_slot.end_time}` : 'Слот не назначен',
                g.schedule_slot && g.schedule_slot.classroom ? `Аудитория: ${g.schedule_slot.classroom}` : '',
                g.id ? { entity: 'course-groups', id: g.id } : null
              ),
              'Группы не созданы.'
            )
          )}
          ${renderSection(
            'Блоки информатики',
            renderMiniGrid(
              data.informatics_blocks,
              (b) => renderMiniCard(
                b.name,
                (b.skills || []).join(', ') || 'Без навыков',
                '',
                b.id ? { entity: 'informatics-blocks', id: b.id } : null
              ),
              'Блоков нет.'
            )
          )}
        `;

      case 'course-categories':
        return `
          ${actions}
          <div class="entity-card-grid">
            ${renderField('Название', data.name)}
            ${renderField('Описание', data.description)}
            ${renderField('Мин. класс', data.min_grade)}
            ${renderField('Макс. класс', data.max_grade)}
            ${renderField('Мин. возраст', data.min_age)}
            ${renderField('Макс. возраст', data.max_age)}
            ${renderField('Уровень образования', data.education_level)}
          </div>
          ${renderSection(
            'Курсы направления',
            renderMiniGrid(
              data.courses,
              (course) => renderMiniCard(
                course.name,
                `Групп: ${course.groups_count || 0}`,
                `Преподавателей: ${(course.teachers || []).length}`,
                course.id ? { entity: 'courses', id: course.id } : null
              ),
              'Курсы не найдены.'
            )
          )}
        `;

      case 'classrooms':
        return `
          ${actions}
          <div class="entity-card-grid">
            ${renderField('Название', data.name)}
            ${renderField('Вместимость', data.capacity)}
            ${renderField('Занятий в аудитории', data.schedule_slots_count)}
          </div>
          ${renderSection('Расписание аудитории', renderScheduleGrid(data.schedule_slots))}
        `;

      case 'informatics-blocks':
        return `
          ${actions}
          <div class="entity-card-grid">
            ${renderField('Название', data.name)}
            ${renderField('Описание', data.description)}
            ${renderField('Курс', data.course ? data.course.name : null)}
            ${renderField('Направление', data.course && data.course.category ? data.course.category.name : null)}
            <div class="entity-field entity-field-wide">
              <div class="entity-field-label">Навыки</div>
              <div class="entity-field-value">${renderTags(data.skills || [])}</div>
            </div>
          </div>
          ${renderSection(
            'Группы блока',
            renderMiniGrid(
              data.groups,
              (g) => renderMiniCard(
                g.label || g.name,
                g.schedule_slot ? `${dayName(g.schedule_slot.day_of_week)} • ${g.schedule_slot.start_time}-${g.schedule_slot.end_time}` : 'Слот не назначен',
                g.schedule_slot && g.schedule_slot.classroom ? `Аудитория: ${g.schedule_slot.classroom}` : '',
                g.id ? { entity: 'course-groups', id: g.id } : null
              ),
              'Группы не найдены.'
            )
          )}
        `;

      case 'schedule-slots':
        return `
          ${actions}
          <div class="entity-card-grid">
            ${renderField('День недели', dayName(data.day_of_week))}
            ${renderField('Начало', data.start_time)}
            ${renderField('Окончание', data.end_time)}
            ${renderField('Группа', data.group ? data.group.label : null)}
            ${renderField('Курс', data.course ? data.course.name : null)}
            ${renderField('Направление', data.category ? data.category.name : null)}
            ${renderField('Преподаватель', data.lead_teacher ? data.lead_teacher.full_name : null)}
            ${renderField('Блок', data.informatics_block ? data.informatics_block.name : null)}
            ${renderField('Аудитория', data.classroom ? data.classroom.name : null)}
          </div>
        `;

      case 'assistant-substitutions':
        return `
          ${actions}
          <div class="entity-card-grid">
            ${renderField('Дата', data.date)}
            ${renderField('Комментарий', data.note)}
            ${renderField('Группа', data.group ? data.group.label : null)}
            ${renderField('Пришедший ассистент', data.substitute ? data.substitute.full_name : null)}
            ${renderField('Кого заменил', data.replaced ? data.replaced.full_name : null)}
          </div>
          ${renderSection(
            'Слот группы',
            data.schedule_slot
              ? renderMiniGrid(
                  [data.schedule_slot],
                  (slot) => renderMiniCard(
                    `${dayName(slot.day_of_week)} • ${slot.start_time}-${slot.end_time}`,
                    slot.classroom || 'Аудитория не назначена',
                    slot.course_name || '',
                    slot.id ? { entity: 'schedule-slots', id: slot.id } : null
                  ),
                  ''
                )
              : renderEmpty('Слот не найден.')
          )}
        `;

      default:
        return `${actions}${renderEmpty('Для этой сущности карточка пока не настроена.')}`;
    }
  }

  function renderDetailHeader(meta, item) {
    return `
      <div class="search-detail-head">
        <div>
          <div class="search-detail-kicker">${escapeHtml(meta.title)}</div>
          <div class="search-detail-title">${escapeHtml(item.label || 'Без названия')}</div>
          <div class="search-detail-id">ID: ${escapeHtml(item.id)}</div>
        </div>
      </div>
    `;
  }

  function renderDetailBody(meta, result) {
    const prettyCard = renderCard(meta, result.data);
    const rawJson = window.syntaxHighlight
      ? window.syntaxHighlight(result.data)
      : escapeHtml(JSON.stringify(result.data, null, 2));

    return `
      <div class="entity-card-wrapper">
        ${prettyCard}
      </div>

      <details class="entity-raw-details">
        <summary>Технический JSON</summary>
        <div class="search-detail-json">
          <pre class="json-display search-detail-pre">${rawJson}</pre>
        </div>
      </details>
    `;
  }

  async function openEntityDetails(meta, item) {
    const detailsBox = document.getElementById('search-explorer-details');
    if (!detailsBox) return;

    window.currentSearchEntity = meta.searchEntity;
    window.currentSearchItemId = item.id;
    window.currentSearchItemLabel = item.label;

    detailsBox.innerHTML = `
      ${renderDetailHeader(meta, item)}
      <div class="search-loading">Загрузка деталей...</div>
    `;

    const result = await fetchJson(window.API_BASE, meta.detailsEndpoint(item.id));
    if (!result.ok) {
      detailsBox.innerHTML = `
        ${renderDetailHeader(meta, item)}
        <div class="search-empty">Не удалось загрузить сущность. HTTP ${escapeHtml(result.status)}</div>
      `;
      if (window.displayResponse) {
        window.displayResponse(meta.detailsEndpoint(item.id), 'GET', result.status, result.data, result.responseTime);
      }
      return;
    }

    detailsBox.innerHTML = `
      ${renderDetailHeader(meta, item)}
      ${renderDetailBody(meta, result)}
    `;

    bindDetailInteractions();

    if (window.displayResponse) {
      window.displayResponse(meta.detailsEndpoint(item.id), 'GET', result.status, result.data, result.responseTime);
    }
  }

  async function navigateToEntity(entity, id) {
    const meta = SEARCH_ENTITIES[entity];
    if (!meta || !id) return;

    if (!canUseManagerSearch() && !PUBLIC_DETAIL_ENTITIES.has(entity)) {
      return;
    }

    const label = `${meta.title} #${id}`;
    await openEntityDetails(meta, { id, label });
  }

  function clearSuggestions(listEl) {
    listEl.innerHTML = '';
    listEl.style.display = 'none';
  }

  function showSuggestions(listEl) {
    listEl.style.display = 'block';
  }

  function markActive(listEl, activeIndex) {
    const nodes = listEl.querySelectorAll('.search-suggestion');
    nodes.forEach((node, idx) => {
      if (idx === activeIndex) node.classList.add('active');
      else node.classList.remove('active');
    });
  }

  function renderSuggestions(listEl, items, onPick) {
    if (!items || items.length === 0) {
      listEl.innerHTML = `<div class="search-empty-row">Ничего не найдено</div>`;
      showSuggestions(listEl);
      return;
    }

    listEl.innerHTML = items.map((item, idx) => `
      <button type="button" class="search-suggestion" data-search-pick="${idx}">
        <span class="search-suggestion-id">#${escapeHtml(item.id)}</span>
        <span class="search-suggestion-text">${escapeHtml(item.label)}</span>
      </button>
    `).join('');

    listEl.querySelectorAll('[data-search-pick]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const idx = parseInt(btn.getAttribute('data-search-pick'), 10);
        const picked = items[idx];
        if (picked) onPick(picked);
      });
    });

    showSuggestions(listEl);
  }

  function attachAutocomplete(inputEl, listEl, meta, opts = {}) {
    const limit = opts.limit || 8;
    let currentItems = [];
    let activeIndex = -1;

    const doSearch = debounce(async () => {
      const q = (inputEl.value || '').trim();

      if (!q) {
        clearSuggestions(listEl);
        setSearchStatus('');
        return;
      }

      listEl.innerHTML = `<div class="search-empty-row">Поиск...</div>`;
      showSuggestions(listEl);

      const result = await fetchJson(window.SEARCH_API_BASE, `/${meta.searchEntity}`, { q, limit });

      if (!result.ok || !Array.isArray(result.data)) {
        currentItems = [];
        activeIndex = -1;
        listEl.innerHTML = `<div class="search-empty-row">Ошибка поиска (HTTP ${result.status})</div>`;
        showSuggestions(listEl);
        setSearchStatus(`Поиск: ${meta.title} — ошибка HTTP ${result.status}`);
        return;
      }

      currentItems = result.data;
      activeIndex = -1;

      renderSuggestions(listEl, currentItems, async (picked) => {
        inputEl.value = picked.label;
        clearSuggestions(listEl);
        setSearchStatus(`Открыт объект: ${meta.title}`);
        await openEntityDetails(meta, picked);
      });

      setSearchStatus(`Найдено: ${currentItems.length} • ${meta.title}`);
    }, 220);

    inputEl.addEventListener('input', doSearch);

    inputEl.addEventListener('keydown', async (e) => {
      if (!currentItems.length) return;

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        activeIndex = (activeIndex + 1) % currentItems.length;
        markActive(listEl, activeIndex);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        activeIndex = activeIndex <= 0 ? currentItems.length - 1 : activeIndex - 1;
        markActive(listEl, activeIndex);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        const picked = currentItems[activeIndex] || currentItems[0];
        if (picked) {
          inputEl.value = picked.label;
          clearSuggestions(listEl);
          setSearchStatus(`Открыт объект: ${meta.title}`);
          await openEntityDetails(meta, picked);
        }
      } else if (e.key === 'Escape') {
        clearSuggestions(listEl);
      }
    });

    document.addEventListener('click', (e) => {
      if (!listEl.contains(e.target) && e.target !== inputEl) {
        clearSuggestions(listEl);
      }
    });
  }

  async function handleDeleteEntity(entity, id) {
    if (!canUseManagerSearch()) return;

    const title = SEARCH_ENTITIES[entity]?.title || entity;
    if (!confirm(`Удалить сущность "${title}" #${id}?`)) return;

    const endpointMap = {
      'students': `/students/${id}`,
      'teachers': `/teachers/${id}`,
      'assistants': `/assistants/${id}`,
      'courses': `/courses/${id}`,
      'course-categories': `/course-categories/${id}`,
      'classrooms': `/classrooms/${id}`,
      'informatics-blocks': `/informatics-blocks/${id}`,
      'schedule-slots': `/schedule/${id}`,
      'assistant-substitutions': `/assistant-substitutions/${id}`
    };

    const endpoint = endpointMap[entity];
    if (!endpoint) {
      alert('Для этой сущности удаление пока не настроено.');
      return;
    }

    const result = await deleteJson(window.API_BASE, endpoint);
    if (window.displayResponse) {
      window.displayResponse(endpoint, 'DELETE', result.status, result.data, result.responseTime);
    }

    if (!result.ok) {
      alert(`Не удалось удалить. HTTP ${result.status}`);
      return;
    }

    const detailsBox = document.getElementById('search-explorer-details');
    if (detailsBox) {
      detailsBox.innerHTML = `<div class="search-empty">Сущность удалена.</div>`;
    }
  }

  async function handleEditEntity(entity, id) {
    if (!canUseManagerSearch()) return;

    const endpointMap = {
      'students': `/students/${id}`,
      'teachers': `/teachers/${id}`,
      'assistants': `/assistants/${id}`,
      'courses': `/courses/${id}`,
      'course-categories': `/course-categories/${id}`,
      'classrooms': `/classrooms/${id}`,
      'informatics-blocks': `/informatics-blocks/${id}`,
      'schedule-slots': `/schedule/${id}`,
      'assistant-substitutions': `/assistant-substitutions/${id}`
    };

    const endpoint = endpointMap[entity];
    if (!endpoint) {
      alert('Для этой сущности редактирование пока не настроено.');
      return;
    }

    let payload = {};

    if (entity === 'students') {
      const phone = prompt('Телефон (пусто = не менять):');
      const email = prompt('Email (пусто = не менять):');
      const address = prompt('Адрес (пусто = не менять):');
      const institution = prompt('Учебное заведение (пусто = не менять):');
      const groupName = prompt('Группа/класс (пусто = не менять):');

      if (phone) payload.phone_number = phone;
      if (email) payload.email = email;
      if (address) payload.address = address;
      if (institution) payload.educational_institution = institution;
      if (groupName) payload.group_name = groupName;
    } else if (entity === 'teachers' || entity === 'assistants') {
      const phone = prompt('Телефон (пусто = не менять):');
      const email = prompt('Email (пусто = не менять):');

      if (phone) payload.phone_number = phone;
      if (email) payload.email = email;
    } else if (entity === 'classrooms') {
      const name = prompt('Название аудитории (пусто = не менять):');
      const capacity = prompt('Вместимость (пусто = не менять):');

      if (name) payload.name = name;
      if (capacity) payload.capacity = parseInt(capacity, 10);
    } else if (entity === 'courses') {
      const name = prompt('Название курса (пусто = не менять):');
      const description = prompt('Описание (пусто = не менять):');
      const maxStudents = prompt('Макс. студентов (пусто = не менять):');
      const duration = prompt('Длительность, мин (пусто = не менять):');
      const price = prompt('Цена (пусто = не менять):');
      const active = prompt('Активен? true/false (пусто = не менять):');

      if (name) payload.name = name;
      if (description) payload.description = description;
      if (maxStudents) payload.max_students = parseInt(maxStudents, 10);
      if (duration) payload.duration_minutes = parseInt(duration, 10);
      if (price) payload.price = parseFloat(price);
      if (active) payload.is_active = active === 'true';
    } else if (entity === 'course-categories') {
      const name = prompt('Название направления (пусто = не менять):');
      const description = prompt('Описание (пусто = не менять):');

      if (name) payload.name = name;
      if (description) payload.description = description;
    } else if (entity === 'informatics-blocks') {
      const name = prompt('Название блока (пусто = не менять):');
      const description = prompt('Описание (пусто = не менять):');
      const skills = prompt('Навыки через запятую (пусто = не менять):');

      if (name) payload.name = name;
      if (description) payload.description = description;
      if (skills) payload.skills = skills.split(',').map((x) => x.trim()).filter(Boolean);
    } else if (entity === 'schedule-slots') {
      const day = prompt('День недели 1-7 (пусто = не менять):');
      const start = prompt('Время начала ЧЧ:ММ (пусто = не менять):');
      const end = prompt('Время окончания ЧЧ:ММ (пусто = не менять):');
      const classroomId = prompt('ID аудитории (пусто = не менять):');

      if (day) payload.day_of_week = parseInt(day, 10);
      if (start) payload.start_time = start;
      if (end) payload.end_time = end;
      if (classroomId) payload.classroom_id = parseInt(classroomId, 10);
    } else if (entity === 'assistant-substitutions') {
      const note = prompt('Комментарий (пусто = не менять):');
      const replaced = prompt('ID заменяемого ассистента (пусто = не менять, null = очистить):');

      if (note) payload.note = note;
      if (replaced) payload.replaced_assistant_id = replaced === 'null' ? null : parseInt(replaced, 10);
    }

    if (!Object.keys(payload).length) return;

    const result = await putJson(window.API_BASE, endpoint, payload);
    if (window.displayResponse) {
      window.displayResponse(endpoint, 'PUT', result.status, result.data, result.responseTime);
    }

    if (!result.ok) {
      alert(`Не удалось сохранить. HTTP ${result.status}`);
      return;
    }

    if (window.currentSearchEntity && window.currentSearchItemId) {
      await navigateToEntity(window.currentSearchEntity, window.currentSearchItemId);
    }
  }

  function bindDetailInteractions() {
    document.querySelectorAll('[data-nav-entity][data-nav-id]').forEach((node) => {
      node.addEventListener('click', async () => {
        const entity = node.getAttribute('data-nav-entity');
        const id = node.getAttribute('data-nav-id');
        await navigateToEntity(entity, id);
      });
    });

    document.querySelectorAll('[data-entity-action="delete"]').forEach((node) => {
      node.addEventListener('click', async () => {
        const entity = node.getAttribute('data-entity');
        const id = node.getAttribute('data-id');
        await handleDeleteEntity(entity, id);
      });
    });

    document.querySelectorAll('[data-entity-action="edit"]').forEach((node) => {
      node.addEventListener('click', async () => {
        const entity = node.getAttribute('data-entity');
        const id = node.getAttribute('data-id');
        await handleEditEntity(entity, id);
      });
    });
  }

  function renderRegistrationColumns(grouped) {
    const columns = [
      ['pending', 'В ожидании'],
      ['approved', 'Одобрено'],
      ['rejected', 'Отклонено'],
      ['completed', 'Завершено']
    ];

    return `
      <div class="registration-board">
        ${columns.map(([statusKey, title]) => {
          const items = grouped[statusKey] || [];
          return `
            <div class="registration-column">
              <div class="registration-column-head">
                <div class="registration-column-title">${escapeHtml(title)}</div>
                <div class="registration-column-count">${items.length}</div>
              </div>
              <div class="registration-column-body">
                ${items.length ? items.map((row) => `
                  <div class="registration-card">
                    <div class="group-card-title">
                      ${escapeHtml(row.student?.full_name || 'Студент')}
                    </div>
                    <div class="group-card-meta">
                      ${escapeHtml(row.course?.name || 'Курс не назначен')}
                    </div>
                    <div class="group-card-meta">
                      ${escapeHtml(row.group?.label || row.group?.name || 'Группа не назначена')}
                    </div>
                    <div class="tag-row">
                      <span class="tag-chip">level: ${escapeHtml(formatValue(row.level))}</span>
                      <span class="tag-chip">id: ${escapeHtml(row.id)}</span>
                    </div>
                  </div>
                `).join('') : `<div class="empty-box">Нет заявок</div>`}
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }

  async function showRegistrationRequests() {
    if (!canUseManagerSearch()) return;

    const box = document.getElementById('registration-requests-section');
    if (!box) return;

    box.innerHTML = `<div class="search-loading">Загрузка заявок...</div>`;

    const result = await fetchJson(window.SEARCH_API_BASE, '/registration-requests', {
      per_status_limit: 20
    });

    if (!result.ok) {
      box.innerHTML = `<div class="search-empty">Не удалось загрузить заявки. HTTP ${result.status}</div>`;
      return;
    }

    box.innerHTML = `
      <div class="registration-section-head">
        <div class="registration-section-title">Заявки на курсы</div>
        <div class="registration-section-meta">Всего: ${escapeHtml(result.data.total || 0)}</div>
      </div>
      ${renderRegistrationColumns(result.data.grouped || {})}
    `;

    if (window.displayResponse) {
      window.displayResponse('/search/registration-requests', 'GET', result.status, result.data, result.responseTime);
    }
  }

  function syncGlobalEntityMeta() {
    const select = document.getElementById('global-search-entity');
    const hint = document.getElementById('global-search-hint');
    const input = document.getElementById('global-search-input');

    if (!select || !hint || !input) return null;

    const meta = SEARCH_ENTITIES[select.value];
    if (!meta) return null;

    hint.textContent = meta.hint;
    input.placeholder = meta.placeholder;
    return meta;
  }

  function initGlobalSearch() {
    if (!canUseManagerSearch()) return;

    const select = document.getElementById('global-search-entity');
    const input = document.getElementById('global-search-input');
    const list = document.getElementById('global-search-suggestions');

    if (!select || !input || !list) return;

    function bindCurrentInput(currentInput) {
      const meta = SEARCH_ENTITIES[select.value];
      if (!meta) return;
      attachAutocomplete(currentInput, list, meta, { limit: 10 });
    }

    function rebind() {
      const meta = syncGlobalEntityMeta();
      if (!meta) return;

      const oldInput = document.getElementById('global-search-input');
      const newInput = oldInput.cloneNode(true);
      oldInput.parentNode.replaceChild(newInput, oldInput);

      newInput.value = '';
      newInput.placeholder = meta.placeholder;
      bindCurrentInput(newInput);
      newInput.focus();
    }

    syncGlobalEntityMeta();
    bindCurrentInput(input);

    select.addEventListener('change', rebind);
  }

  function initPresetButtons() {
    if (!canUseManagerSearch()) return;

    document.querySelectorAll('[data-search-preset]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const entity = btn.getAttribute('data-search-preset');
        const select = document.getElementById('global-search-entity');
        if (!select || !SEARCH_ENTITIES[entity]) return;

        select.value = entity;
        select.dispatchEvent(new Event('change'));

        setTimeout(() => {
          const refreshedInput = document.getElementById('global-search-input');
          if (refreshedInput) refreshedInput.focus();
        }, 30);
      });
    });

    const requestsBtn = document.getElementById('show-registration-requests-btn');
    if (requestsBtn) {
      requestsBtn.addEventListener('click', showRegistrationRequests);
    }
  }

  async function searchStudentsInGroup() {
    if (!canUseGroupStudents()) return;

    const groupIdInput = document.getElementById('group-students-group-id');
    const queryInput = document.getElementById('group-students-query');
    const resultBox = document.getElementById('group-students-results');

    if (!groupIdInput || !queryInput || !resultBox) return;

    const groupId = (groupIdInput.value || '').trim();
    const q = (queryInput.value || '').trim();

    if (!groupId) {
      resultBox.innerHTML = `<div class="search-empty">Сначала укажи group_id.</div>`;
      return;
    }

    resultBox.innerHTML = `<div class="search-loading">Ищем студентов группы...</div>`;

    const result = await fetchJson(window.SEARCH_API_BASE, '/group-students', {
      group_id: groupId,
      q,
      limit: 30
    });

    if (!result.ok || !Array.isArray(result.data)) {
      resultBox.innerHTML = `<div class="search-empty">Ошибка поиска студентов группы. HTTP ${result.status}</div>`;
      return;
    }

    if (!result.data.length) {
      resultBox.innerHTML = `<div class="search-empty">По этому запросу студенты не найдены.</div>`;
      return;
    }

    resultBox.innerHTML = result.data.map((item, index) => `
      <button type="button" class="group-student-row" data-group-student-index="${index}">
        <span class="group-student-id">#${escapeHtml(item.id)}</span>
        <span class="group-student-label">${escapeHtml(item.label)}</span>
      </button>
    `).join('');

    resultBox.querySelectorAll('[data-group-student-index]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const index = parseInt(btn.getAttribute('data-group-student-index'), 10);
        const item = result.data[index];
        if (!item) return;

        if (canUseManagerSearch()) {
          const meta = SEARCH_ENTITIES['students'];
          await openEntityDetails(meta, item);
          return;
        }

        if (window.displayResponse) {
          window.displayResponse(
            '/search/group-students',
            'GET',
            200,
            item,
            result.responseTime
          );
        }
      });
    });
  }

  function initGroupStudentsSearch() {
    if (!canUseGroupStudents()) return;

    const groupIdInput = document.getElementById('group-students-group-id');
    const queryInput = document.getElementById('group-students-query');
    const searchBtn = document.getElementById('group-students-search-btn');
    const useSelectedBtn = document.getElementById('group-students-use-selected');

    if (!groupIdInput || !queryInput || !searchBtn || !useSelectedBtn) return;

    searchBtn.addEventListener('click', searchStudentsInGroup);

    queryInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        searchStudentsInGroup();
      }
    });

    useSelectedBtn.addEventListener('click', () => {
      if (window.currentSearchGroupId) {
        groupIdInput.value = String(window.currentSearchGroupId);
      }
    });
  }

  function initSearchExplorer() {
    const detailsBox = document.getElementById('search-explorer-details');
    if (detailsBox) {
      detailsBox.innerHTML = canUseManagerSearch()
        ? `<div class="search-empty">Выбери сущность через поиск сверху.</div>`
        : `<div class="search-empty">Детальный просмотр доступен менеджеру и администратору.</div>`;
    }

    initGlobalSearch();
    initPresetButtons();
    initGroupStudentsSearch();
  }

  document.addEventListener('DOMContentLoaded', initSearchExplorer);

  window.escapeHtml = escapeHtml;
  window.formatValue = formatValue;
})();
