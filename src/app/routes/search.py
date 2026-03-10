from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload

from src.app.services.smart_search import build_query_variants, rank

from src.app.models import (
    Student,
    Parent,
    Teacher,
    Assistant,
    CourseCategory,
    Course,
    InformaticsBlock,
    CourseGroup,
    Classroom,
    ScheduleSlot,
    AssistantSubstitution,
    CourseRegistration,
    StudentPreference,
    StudentRegistration,
)

search_bp = Blueprint("search", __name__)


REGISTRATION_STATUS_RU = {
    "pending": "В ожидании",
    "approved": "Одобрено",
    "rejected": "Отклонено",
    "completed": "Завершено",
}


def _full_name(obj):
    parts = [
        getattr(obj, "lastname", None),
        getattr(obj, "firstname", None),
        getattr(obj, "surname", None),
    ]
    return " ".join([p for p in parts if p])


def _fmt_datetime(value):
    return value.isoformat() if value else None


def _fmt_date(value):
    return value.isoformat() if value else None


def _fmt_time(value):
    return value.strftime("%H:%M") if value else None


def _label_course(c: Course) -> str:
    cat = c.category.name if getattr(c, "category", None) else None
    return f"{c.name}" + (f" (кат: {cat})" if cat else "")


def _label_category(x: CourseCategory) -> str:
    extra = []
    if x.min_grade is not None and x.max_grade is not None:
        extra.append(f"{x.min_grade}-{x.max_grade} кл")
    if x.education_level:
        extra.append(str(x.education_level))
    return f"{x.name}" + (f" ({', '.join(extra)})" if extra else "")


def _label_teacher(t: Teacher) -> str:
    email = f" — {t.email}" if getattr(t, "email", None) else ""
    return f"{_full_name(t)}{email}"


def _label_assistant(a: Assistant) -> str:
    email = f" — {a.email}" if getattr(a, "email", None) else ""
    phone = f" — {a.phone_number}" if getattr(a, "phone_number", None) else ""
    return f"{_full_name(a)}{email}{phone}"


def _label_student(s: Student) -> str:
    edu = getattr(s, "educational_institution", None)
    grp = getattr(s, "group_name", None)
    return f"{_full_name(s)} — {edu or ''} {grp or ''}".strip()


def _label_group(g: CourseGroup) -> str:
    course_name = g.course.name if getattr(g, "course", None) else None
    category_name = (
        g.course.category.name
        if getattr(g, "course", None) and getattr(g.course, "category", None)
        else None
    )
    teacher_name = _full_name(g.lead_teacher) if getattr(g, "lead_teacher", None) else None
    block_name = g.informatics_block.name if getattr(g, "informatics_block", None) else None

    extra = []
    if course_name:
        extra.append(course_name)
    if category_name:
        extra.append(f"кат: {category_name}")
    if teacher_name:
        extra.append(f"преп: {teacher_name}")
    if block_name:
        extra.append(f"блок: {block_name}")

    return f"{g.name} {g.academic_year}" + (f" — {' — '.join(extra)}" if extra else "")


def _label_classroom(c: Classroom) -> str:
    return f"{c.name} ({c.capacity} мест)"


def _label_block(b: InformaticsBlock) -> str:
    course_name = b.course.name if getattr(b, "course", None) else f"course_id={b.course_id}"
    return f"{b.name} — {course_name}"


def _label_slot(s: ScheduleSlot) -> str:
    group = getattr(s, "group", None)
    course_name = group.course.name if group and getattr(group, "course", None) else None
    group_name = group.name if group else f"group_id={s.group_id}"
    room = s.classroom.name if getattr(s, "classroom", None) else None
    day = s.day_of_week
    st = _fmt_time(s.start_time)
    en = _fmt_time(s.end_time)

    return (
        f"день={day} {st}-{en} — {group_name}"
        + (f" — {course_name}" if course_name else "")
        + (f" — {room}" if room else "")
    )


def _label_subst(x: AssistantSubstitution) -> str:
    group = getattr(x, "group", None)
    group_name = group.name if group else f"group_id={x.group_id}"
    return f"{x.date} — {group_name} (sub={x.substitute_assistant_id}, repl={x.replaced_assistant_id})"


def _label_registration_request(r: CourseRegistration) -> str:
    student_name = _full_name(r.student) if getattr(r, "student", None) else f"student_id={r.student_id}"
    course_name = r.course.name if getattr(r, "course", None) else "курс не назначен"
    group_name = r.group.name if getattr(r, "group", None) else "группа не назначена"
    status_ru = REGISTRATION_STATUS_RU.get(r.status, r.status)
    return f"{student_name} — {course_name} — {group_name} — {status_ru}"


def _serialize_search_item(item, label_fn):
    return {
        "id": item.id,
        "label": label_fn(item)
    }


def _category_summary(x: CourseCategory | None):
    if not x:
        return None
    return {
        "id": x.id,
        "name": x.name,
        "description": x.description,
        "min_grade": x.min_grade,
        "max_grade": x.max_grade,
        "min_age": x.min_age,
        "max_age": x.max_age,
        "education_level": x.education_level,
        "label": _label_category(x),
    }


def _course_summary(c: Course | None):
    if not c:
        return None
    return {
        "id": c.id,
        "name": c.name,
        "description": c.description,
        "category_id": c.category_id,
        "category": c.category.name if getattr(c, "category", None) else None,
        "max_students": c.max_students,
        "use_classroom_capacity": c.use_classroom_capacity,
        "duration_minutes": c.duration_minutes,
        "price": float(c.price) if c.price is not None else None,
        "is_active": c.is_active,
        "label": _label_course(c),
    }


def _teacher_summary(t: Teacher | None):
    if not t:
        return None
    return {
        "id": t.id,
        "full_name": _full_name(t),
        "firstname": t.firstname,
        "lastname": t.lastname,
        "surname": t.surname,
        "birthday": _fmt_date(t.birthday),
        "phone_number": t.phone_number,
        "email": t.email,
        "created_at": _fmt_datetime(getattr(t, "created_at", None)),
        "label": _label_teacher(t),
    }


def _assistant_summary(a: Assistant | None):
    if not a:
        return None
    return {
        "id": a.id,
        "full_name": _full_name(a),
        "firstname": a.firstname,
        "lastname": a.lastname,
        "surname": a.surname,
        "birthday": _fmt_date(a.birthday),
        "phone_number": a.phone_number,
        "email": a.email,
        "created_at": _fmt_datetime(getattr(a, "created_at", None)),
        "label": _label_assistant(a),
    }


def _student_summary(s: Student | None):
    if not s:
        return None
    return {
        "id": s.id,
        "full_name": _full_name(s),
        "firstname": s.firstname,
        "lastname": s.lastname,
        "surname": s.surname,
        "phone_number": s.phone_number,
        "email": s.email,
        "birthday": _fmt_date(s.birthday),
        "address": s.address,
        "educational_institution": s.educational_institution,
        "group_name": s.group_name,
        "education_type": s.education_type,
        "enrolled_this_year": s.enrolled_this_year,
        "created_at": _fmt_datetime(getattr(s, "created_at", None)),
        "label": _label_student(s),
    }


def _parent_summary(p: Parent | None):
    if not p:
        return None
    return {
        "id": p.id,
        "full_name": _full_name(p),
        "firstname": p.firstname,
        "lastname": p.lastname,
        "surname": p.surname,
        "birthday": _fmt_date(p.birthday),
        "address": p.address,
        "phone_number": p.phone_number,
        "email": p.email,
        "data_processing_consent": p.data_processing_consent,
        "created_at": _fmt_datetime(getattr(p, "created_at", None)),
    }


def _classroom_summary(c: Classroom | None):
    if not c:
        return None
    return {
        "id": c.id,
        "name": c.name,
        "capacity": c.capacity,
        "label": _label_classroom(c),
    }


def _block_summary(b: InformaticsBlock | None):
    if not b:
        return None
    return {
        "id": b.id,
        "course_id": b.course_id,
        "name": b.name,
        "description": b.description,
        "skills": list(b.skills or []),
        "created_at": _fmt_datetime(getattr(b, "created_at", None)),
        "label": _label_block(b),
    }


def _slot_summary(s: ScheduleSlot | None):
    if not s:
        return None
    return {
        "id": s.id,
        "group_id": s.group_id,
        "day_of_week": s.day_of_week,
        "start_time": _fmt_time(s.start_time),
        "end_time": _fmt_time(s.end_time),
        "classroom_id": s.classroom_id,
        "classroom": s.classroom.name if getattr(s, "classroom", None) else None,
        "classroom_capacity": s.classroom.capacity if getattr(s, "classroom", None) else None,
        "group_name": s.group.name if getattr(s, "group", None) else None,
        "course_name": (
            s.group.course.name
            if getattr(s, "group", None) and getattr(s.group, "course", None)
            else None
        ),
        "teacher_name": (
            _full_name(s.group.lead_teacher)
            if getattr(s, "group", None) and getattr(s.group, "lead_teacher", None)
            else None
        ),
        "label": _label_slot(s),
    }


def _group_summary(g: CourseGroup | None):
    if not g:
        return None
    return {
        "id": g.id,
        "name": g.name,
        "academic_year": g.academic_year,
        "course_id": g.course_id,
        "course_name": g.course.name if getattr(g, "course", None) else None,
        "category_name": (
            g.course.category.name
            if getattr(g, "course", None) and getattr(g.course, "category", None)
            else None
        ),
        "lead_teacher_id": g.lead_teacher_id,
        "lead_teacher_name": _full_name(g.lead_teacher) if getattr(g, "lead_teacher", None) else None,
        "block_id": g.block_id,
        "block_name": g.informatics_block.name if getattr(g, "informatics_block", None) else None,
        "is_active": g.is_active,
        "min_level": g.min_level,
        "max_level": g.max_level,
        "max_students_override": g.max_students_override,
        "created_at": _fmt_datetime(getattr(g, "created_at", None)),
        "label": _label_group(g),
    }


def _preference_summary(p: StudentPreference | None):
    if not p:
        return None
    return {
        "id": p.id,
        "preference_text": p.preference_text,
        "processed": p.processed,
        "matched_courses": list(p.matched_courses or []),
        "created_at": _fmt_datetime(getattr(p, "created_at", None)),
    }


def _registration_summary(r: CourseRegistration | None):
    if not r:
        return None
    return {
        "id": r.id,
        "status": r.status,
        "status_ru": REGISTRATION_STATUS_RU.get(r.status, r.status),
        "comment": r.comment,
        "level": r.level,
        "skills": list(r.skills or []),
        "created_at": _fmt_datetime(getattr(r, "created_at", None)),
        "completed_at": _fmt_datetime(getattr(r, "completed_at", None)),
        "course": _course_summary(r.course),
        "category": _category_summary(r.category),
        "group": _group_summary(r.group),
        "preferred_slot": _slot_summary(r.preferred_slot),
        "block": _block_summary(r.block),
        "preference": _preference_summary(r.preference),
        "student": _student_summary(r.student),
    }


ENTITY = {
    "courses": {
        "model": Course,
        "label": _label_course,
        "options": [joinedload(Course.category)],
        "order": Course.id.asc(),
    },
    "course-categories": {
        "model": CourseCategory,
        "label": _label_category,
        "order": CourseCategory.id.asc(),
    },
    "teachers": {
        "model": Teacher,
        "label": _label_teacher,
        "order": Teacher.id.asc(),
    },
    "assistants": {
        "model": Assistant,
        "label": _label_assistant,
        "order": Assistant.id.asc(),
    },
    "students": {
        "model": Student,
        "label": _label_student,
        "order": Student.id.asc(),
    },
    "course-groups": {
        "model": CourseGroup,
        "label": _label_group,
        "options": [
            joinedload(CourseGroup.course).joinedload(Course.category),
            joinedload(CourseGroup.lead_teacher),
            joinedload(CourseGroup.informatics_block),
        ],
        "order": CourseGroup.id.asc(),
    },
    "classrooms": {
        "model": Classroom,
        "label": _label_classroom,
        "order": Classroom.id.asc(),
    },
    "informatics-blocks": {
        "model": InformaticsBlock,
        "label": _label_block,
        "options": [joinedload(InformaticsBlock.course)],
        "order": InformaticsBlock.id.asc(),
    },
    "assistant-substitutions": {
        "model": AssistantSubstitution,
        "label": _label_subst,
        "options": [joinedload(AssistantSubstitution.group)],
        "order": AssistantSubstitution.id.asc(),
    },
    "schedule-slots": {
        "model": ScheduleSlot,
        "label": _label_slot,
        "options": [
            joinedload(ScheduleSlot.group).joinedload(CourseGroup.course),
            joinedload(ScheduleSlot.classroom),
        ],
        "order": ScheduleSlot.id.asc(),
    },
}


def _base_query_for_entity(cfg):
    query = cfg["model"].query
    for opt in cfg.get("options", []) or []:
        query = query.options(opt)
    return query


def _student_detail_query():
    return (
        Student.query
        .options(joinedload(Student.preferences))
        .options(
            joinedload(Student.registrations)
            .joinedload(CourseRegistration.course)
            .joinedload(Course.category)
        )
        .options(joinedload(Student.registrations).joinedload(CourseRegistration.category))
        .options(
            joinedload(Student.registrations)
            .joinedload(CourseRegistration.group)
            .joinedload(CourseGroup.course)
            .joinedload(Course.category)
        )
        .options(joinedload(Student.registrations).joinedload(CourseRegistration.group).joinedload(CourseGroup.lead_teacher))
        .options(joinedload(Student.registrations).joinedload(CourseRegistration.preferred_slot).joinedload(ScheduleSlot.classroom))
        .options(joinedload(Student.registrations).joinedload(CourseRegistration.block).joinedload(InformaticsBlock.course))
        .options(joinedload(Student.registrations).joinedload(CourseRegistration.preference))
        .options(joinedload(Student.registrations).joinedload(CourseRegistration.student))
        .options(joinedload(Student.parent_registrations).joinedload(StudentRegistration.parent))
    )


def _teacher_detail_query():
    return (
        Teacher.query
        .options(joinedload(Teacher.allowed_courses).joinedload(Course.category))
        .options(joinedload(Teacher.lead_groups).joinedload(CourseGroup.course).joinedload(Course.category))
        .options(joinedload(Teacher.lead_groups).joinedload(CourseGroup.informatics_block))
        .options(joinedload(Teacher.lead_groups).joinedload(CourseGroup.schedule_slot).joinedload(ScheduleSlot.classroom))
    )


def _assistant_detail_query():
    return (
        Assistant.query
        .options(joinedload(Assistant.groups).joinedload(CourseGroup.course).joinedload(Course.category))
        .options(joinedload(Assistant.groups).joinedload(CourseGroup.schedule_slot).joinedload(ScheduleSlot.classroom))
    )


def _course_detail_query():
    return (
        Course.query
        .options(joinedload(Course.category))
        .options(joinedload(Course.allowed_teachers))
        .options(joinedload(Course.groups).joinedload(CourseGroup.lead_teacher))
        .options(joinedload(Course.groups).joinedload(CourseGroup.informatics_block))
        .options(joinedload(Course.groups).joinedload(CourseGroup.schedule_slot).joinedload(ScheduleSlot.classroom))
        .options(joinedload(Course.informatics_blocks))
    )


def _category_detail_query():
    return (
        CourseCategory.query
        .options(joinedload(CourseCategory.courses).joinedload(Course.allowed_teachers))
        .options(joinedload(CourseCategory.courses).joinedload(Course.groups))
    )


def _group_detail_query():
    return (
        CourseGroup.query
        .options(joinedload(CourseGroup.course).joinedload(Course.category))
        .options(joinedload(CourseGroup.lead_teacher))
        .options(joinedload(CourseGroup.informatics_block).joinedload(InformaticsBlock.course))
        .options(joinedload(CourseGroup.assistants))
        .options(joinedload(CourseGroup.schedule_slot).joinedload(ScheduleSlot.classroom))
        .options(
            joinedload(CourseGroup.registrations)
            .joinedload(CourseRegistration.student)
        )
        .options(joinedload(CourseGroup.registrations).joinedload(CourseRegistration.preferred_slot).joinedload(ScheduleSlot.classroom))
    )


def _classroom_detail_query():
    return (
        Classroom.query
        .options(
            joinedload(Classroom.schedule_slots)
            .joinedload(ScheduleSlot.group)
            .joinedload(CourseGroup.course)
            .joinedload(Course.category)
        )
        .options(joinedload(Classroom.schedule_slots).joinedload(ScheduleSlot.group).joinedload(CourseGroup.lead_teacher))
    )


def _block_detail_query():
    return (
        InformaticsBlock.query
        .options(joinedload(InformaticsBlock.course).joinedload(Course.category))
        .options(joinedload(InformaticsBlock.groups).joinedload(CourseGroup.lead_teacher))
        .options(joinedload(InformaticsBlock.groups).joinedload(CourseGroup.schedule_slot).joinedload(ScheduleSlot.classroom))
    )


def _slot_detail_query():
    return (
        ScheduleSlot.query
        .options(joinedload(ScheduleSlot.classroom))
        .options(joinedload(ScheduleSlot.group).joinedload(CourseGroup.course).joinedload(Course.category))
        .options(joinedload(ScheduleSlot.group).joinedload(CourseGroup.lead_teacher))
        .options(joinedload(ScheduleSlot.group).joinedload(CourseGroup.informatics_block))
    )


def _substitution_detail_query():
    return (
        AssistantSubstitution.query
        .options(joinedload(AssistantSubstitution.group).joinedload(CourseGroup.course).joinedload(Course.category))
        .options(joinedload(AssistantSubstitution.group).joinedload(CourseGroup.schedule_slot).joinedload(ScheduleSlot.classroom))
        .options(joinedload(AssistantSubstitution.substitute))
        .options(joinedload(AssistantSubstitution.replaced))
    )


def _registration_requests_query():
    return (
        CourseRegistration.query
        .options(joinedload(CourseRegistration.student))
        .options(joinedload(CourseRegistration.course).joinedload(Course.category))
        .options(joinedload(CourseRegistration.category))
        .options(joinedload(CourseRegistration.group).joinedload(CourseGroup.course).joinedload(Course.category))
        .options(joinedload(CourseRegistration.group).joinedload(CourseGroup.lead_teacher))
        .options(joinedload(CourseRegistration.preferred_slot).joinedload(ScheduleSlot.classroom))
        .options(joinedload(CourseRegistration.block).joinedload(InformaticsBlock.course))
        .options(joinedload(CourseRegistration.preference))
    )


def _student_detail_payload(s: Student):
    parents = [
        _parent_summary(link.parent)
        for link in (s.parent_registrations or [])
        if link.parent
    ]

    registrations = [
        _registration_summary(reg)
        for reg in sorted(s.registrations or [], key=lambda x: x.id)
    ]

    preferences = [
        _preference_summary(pref)
        for pref in sorted(s.preferences or [], key=lambda x: x.id)
    ]

    return {
        "id": s.id,
        "label": _label_student(s),
        "full_name": _full_name(s),
        "firstname": s.firstname,
        "lastname": s.lastname,
        "surname": s.surname,
        "phone_number": s.phone_number,
        "email": s.email,
        "birthday": _fmt_date(s.birthday),
        "address": s.address,
        "educational_institution": s.educational_institution,
        "group_name": s.group_name,
        "education_type": s.education_type,
        "enrolled_this_year": s.enrolled_this_year,
        "created_at": _fmt_datetime(getattr(s, "created_at", None)),
        "parents": parents,
        "preferences": preferences,
        "registrations": registrations,
    }


def _teacher_detail_payload(t: Teacher):
    allowed_courses = [
        _course_summary(course)
        for course in sorted(t.allowed_courses or [], key=lambda x: x.id)
    ]

    lead_groups = [
        {
            **_group_summary(group),
            "schedule_slot": _slot_summary(group.schedule_slot)
        }
        for group in sorted(t.lead_groups or [], key=lambda x: x.id)
    ]

    return {
        "id": t.id,
        "label": _label_teacher(t),
        "full_name": _full_name(t),
        "firstname": t.firstname,
        "lastname": t.lastname,
        "surname": t.surname,
        "birthday": _fmt_date(t.birthday),
        "phone_number": t.phone_number,
        "email": t.email,
        "created_at": _fmt_datetime(getattr(t, "created_at", None)),
        "allowed_courses": allowed_courses,
        "lead_groups": lead_groups,
    }


def _assistant_detail_payload(a: Assistant):
    groups = [
        {
            **_group_summary(group),
            "schedule_slot": _slot_summary(group.schedule_slot)
        }
        for group in sorted(a.groups or [], key=lambda x: x.id)
    ]

    return {
        "id": a.id,
        "label": _label_assistant(a),
        "full_name": _full_name(a),
        "firstname": a.firstname,
        "lastname": a.lastname,
        "surname": a.surname,
        "birthday": _fmt_date(a.birthday),
        "phone_number": a.phone_number,
        "email": a.email,
        "created_at": _fmt_datetime(getattr(a, "created_at", None)),
        "groups": groups,
    }


def _course_detail_payload(c: Course):
    groups = [
        {
            **_group_summary(group),
            "schedule_slot": _slot_summary(group.schedule_slot)
        }
        for group in sorted(c.groups or [], key=lambda x: x.id)
    ]

    return {
        "id": c.id,
        "label": _label_course(c),
        "name": c.name,
        "description": c.description,
        "category": _category_summary(c.category),
        "max_students": c.max_students,
        "use_classroom_capacity": c.use_classroom_capacity,
        "duration_minutes": c.duration_minutes,
        "price": float(c.price) if c.price is not None else None,
        "is_active": c.is_active,
        "created_at": _fmt_datetime(getattr(c, "created_at", None)),
        "allowed_teachers": [
            _teacher_summary(t) for t in sorted(c.allowed_teachers or [], key=lambda x: x.id)
        ],
        "groups": groups,
        "informatics_blocks": [
            _block_summary(b) for b in sorted(c.informatics_blocks or [], key=lambda x: x.id)
        ],
        "groups_count": len(c.groups or []),
        "teachers_count": len(c.allowed_teachers or []),
    }


def _category_detail_payload(cat: CourseCategory):
    courses = [
        {
            **_course_summary(c),
            "teachers": [_teacher_summary(t) for t in sorted(c.allowed_teachers or [], key=lambda x: x.id)],
            "groups_count": len(c.groups or []),
        }
        for c in sorted(cat.courses or [], key=lambda x: x.id)
    ]

    return {
        "id": cat.id,
        "label": _label_category(cat),
        "name": cat.name,
        "description": cat.description,
        "min_grade": cat.min_grade,
        "max_grade": cat.max_grade,
        "min_age": cat.min_age,
        "max_age": cat.max_age,
        "education_level": cat.education_level,
        "created_at": _fmt_datetime(getattr(cat, "created_at", None)),
        "courses": courses,
        "courses_count": len(cat.courses or []),
    }


def _group_detail_payload(g: CourseGroup):
    students = []
    for reg in sorted(g.registrations or [], key=lambda x: x.id):
        if reg.student:
            students.append({
                "registration_id": reg.id,
                "status": reg.status,
                "status_ru": REGISTRATION_STATUS_RU.get(reg.status, reg.status),
                "level": reg.level,
                "comment": reg.comment,
                "student": _student_summary(reg.student),
                "preferred_slot": _slot_summary(reg.preferred_slot),
            })

    return {
        "id": g.id,
        "label": _label_group(g),
        "name": g.name,
        "academic_year": g.academic_year,
        "is_active": g.is_active,
        "min_level": g.min_level,
        "max_level": g.max_level,
        "max_students_override": g.max_students_override,
        "created_at": _fmt_datetime(getattr(g, "created_at", None)),
        "course": _course_summary(g.course),
        "category": _category_summary(g.course.category) if getattr(g, "course", None) and getattr(g.course, "category", None) else None,
        "lead_teacher": _teacher_summary(g.lead_teacher),
        "informatics_block": _block_summary(g.informatics_block),
        "assistants": [_assistant_summary(a) for a in sorted(g.assistants or [], key=lambda x: x.id)],
        "schedule_slot": _slot_summary(g.schedule_slot),
        "students": students,
        "students_count": len(students),
        "assistants_count": len(g.assistants or []),
    }


def _classroom_detail_payload(c: Classroom):
    slots = sorted(
        c.schedule_slots or [],
        key=lambda x: (
            x.day_of_week or 0,
            _fmt_time(x.start_time) or "",
            x.id
        )
    )

    return {
        "id": c.id,
        "label": _label_classroom(c),
        "name": c.name,
        "capacity": c.capacity,
        "schedule_slots": [
            {
                **_slot_summary(slot),
                "group": _group_summary(slot.group),
            }
            for slot in slots
        ],
        "schedule_slots_count": len(slots),
    }


def _block_detail_payload(b: InformaticsBlock):
    groups = [
        {
            **_group_summary(group),
            "schedule_slot": _slot_summary(group.schedule_slot)
        }
        for group in sorted(b.groups or [], key=lambda x: x.id)
    ]

    return {
        "id": b.id,
        "label": _label_block(b),
        "name": b.name,
        "description": b.description,
        "skills": list(b.skills or []),
        "created_at": _fmt_datetime(getattr(b, "created_at", None)),
        "course": _course_summary(b.course),
        "groups": groups,
        "groups_count": len(groups),
    }


def _slot_detail_payload(s: ScheduleSlot):
    return {
        "id": s.id,
        "label": _label_slot(s),
        "day_of_week": s.day_of_week,
        "start_time": _fmt_time(s.start_time),
        "end_time": _fmt_time(s.end_time),
        "group": _group_summary(s.group),
        "course": _course_summary(s.group.course) if getattr(s, "group", None) and getattr(s.group, "course", None) else None,
        "category": (
            _category_summary(s.group.course.category)
            if getattr(s, "group", None) and getattr(s.group, "course", None) and getattr(s.group.course, "category", None)
            else None
        ),
        "lead_teacher": _teacher_summary(s.group.lead_teacher) if getattr(s, "group", None) and getattr(s.group, "lead_teacher", None) else None,
        "informatics_block": _block_summary(s.group.informatics_block) if getattr(s, "group", None) and getattr(s.group, "informatics_block", None) else None,
        "classroom": _classroom_summary(s.classroom),
    }


def _substitution_detail_payload(x: AssistantSubstitution):
    return {
        "id": x.id,
        "label": _label_subst(x),
        "date": _fmt_date(x.date),
        "note": x.note,
        "created_at": _fmt_datetime(getattr(x, "created_at", None)),
        "group": _group_summary(x.group),
        "schedule_slot": _slot_summary(x.group.schedule_slot) if getattr(x, "group", None) and getattr(x.group, "schedule_slot", None) else None,
        "substitute": _assistant_summary(x.substitute),
        "replaced": _assistant_summary(x.replaced),
    }


DETAIL_MAP = {
    "students": {
        "query_builder": _student_detail_query,
        "payload_builder": _student_detail_payload,
    },
    "teachers": {
        "query_builder": _teacher_detail_query,
        "payload_builder": _teacher_detail_payload,
    },
    "assistants": {
        "query_builder": _assistant_detail_query,
        "payload_builder": _assistant_detail_payload,
    },
    "courses": {
        "query_builder": _course_detail_query,
        "payload_builder": _course_detail_payload,
    },
    "course-categories": {
        "query_builder": _category_detail_query,
        "payload_builder": _category_detail_payload,
    },
    "course-groups": {
        "query_builder": _group_detail_query,
        "payload_builder": _group_detail_payload,
    },
    "classrooms": {
        "query_builder": _classroom_detail_query,
        "payload_builder": _classroom_detail_payload,
    },
    "informatics-blocks": {
        "query_builder": _block_detail_query,
        "payload_builder": _block_detail_payload,
    },
    "schedule-slots": {
        "query_builder": _slot_detail_query,
        "payload_builder": _slot_detail_payload,
    },
    "assistant-substitutions": {
        "query_builder": _substitution_detail_query,
        "payload_builder": _substitution_detail_payload,
    },
}


@search_bp.route("/_entities", methods=["GET"])
def entities():
    return jsonify(sorted(list(ENTITY.keys())))


@search_bp.route("/group-students", methods=["GET"], strict_slashes=False)
def search_group_students():
    group_id = request.args.get("group_id", type=int)
    q_raw = (request.args.get("q") or "").strip()
    limit = request.args.get("limit", type=int) or 10
    limit = max(1, min(limit, 50))

    if not group_id:
        return jsonify({"error": "group_id is required"}), 400

    regs = (
        CourseRegistration.query
        .options(joinedload(CourseRegistration.student))
        .filter(CourseRegistration.group_id == group_id)
        .all()
    )

    students_map = {}
    for reg in regs:
        if reg.student:
            students_map[reg.student.id] = reg.student

    students = list(students_map.values())

    if not q_raw:
        students = sorted(students, key=lambda s: s.id)[:limit]
        return jsonify([_serialize_search_item(s, _label_student) for s in students])

    variants = build_query_variants(q_raw)
    ranked = rank(students, variants, _label_student)
    ranked = ranked[:limit]

    return jsonify([_serialize_search_item(s, _label_student) for s in ranked])


@search_bp.route("/registration-requests", methods=["GET"], strict_slashes=False)
def registration_requests():
    q_raw = (request.args.get("q") or "").strip()
    course_id = request.args.get("course_id", type=int)
    group_id = request.args.get("group_id", type=int)
    status_filter = (request.args.get("status") or "").strip()
    per_status_limit = request.args.get("per_status_limit", type=int) or 20
    per_status_limit = max(1, min(per_status_limit, 100))

    query = _registration_requests_query()

    if course_id:
        query = query.filter(CourseRegistration.course_id == course_id)
    if group_id:
        query = query.filter(CourseRegistration.group_id == group_id)
    if status_filter:
        query = query.filter(CourseRegistration.status == status_filter)

    items = query.order_by(CourseRegistration.id.desc()).all()

    if q_raw:
        variants = build_query_variants(q_raw)
        items = rank(items, variants, _label_registration_request)

    grouped = {
        "pending": [],
        "approved": [],
        "rejected": [],
        "completed": [],
    }

    for item in items:
        if item.status in grouped and len(grouped[item.status]) < per_status_limit:
            grouped[item.status].append(_registration_summary(item))

    counts = {
        status: len([x for x in items if x.status == status])
        for status in grouped.keys()
    }

    return jsonify({
        "total": len(items),
        "counts": counts,
        "statuses_ru": REGISTRATION_STATUS_RU,
        "grouped": grouped,
    })


@search_bp.route("/details/<entity>/<int:item_id>", methods=["GET"], strict_slashes=False)
def details(entity: str, item_id: int):
    cfg = DETAIL_MAP.get(entity)
    if not cfg:
        return jsonify({
            "error": f"Unknown detail entity '{entity}'",
            "entities": sorted(list(DETAIL_MAP.keys()))
        }), 404

    item = cfg["query_builder"]().get(item_id)
    if not item:
        return jsonify({"error": f"{entity} item with id={item_id} not found"}), 404

    return jsonify(cfg["payload_builder"](item))


@search_bp.route("/<entity>", methods=["GET"], strict_slashes=False)
def search(entity: str):
    cfg = ENTITY.get(entity)
    if not cfg:
        return jsonify({
            "error": f"Unknown entity '{entity}'",
            "entities": sorted(list(ENTITY.keys()))
        }), 404

    q_raw = (request.args.get("q") or "").strip()
    limit = request.args.get("limit", type=int) or 10
    limit = max(1, min(limit, 50))

    label_fn = cfg["label"]
    query = _base_query_for_entity(cfg)

    if not q_raw:
        items = query.order_by(cfg["order"]).limit(limit).all()
        return jsonify([_serialize_search_item(item, label_fn) for item in items])

    variants = build_query_variants(q_raw)
    candidates = query.order_by(cfg["order"]).limit(2000).all()
    ranked = rank(candidates, variants, label_fn)
    ranked = ranked[:limit]

    return jsonify([_serialize_search_item(item, label_fn) for item in ranked])