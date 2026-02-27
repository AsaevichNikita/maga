from flask import Blueprint, request, Response
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import json

from src.app import db
from src.app.models import (
    Student, Course, CourseCategory, CourseGroup, ScheduleSlot, Classroom,
    CourseRegistration, InformaticsBlock
)

registration_bp = Blueprint("registration", __name__, url_prefix="/registration")


def json_response(data, status=200):
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype="application/json; charset=utf-8",
        status=status
    )


def time_overlap(a_start, a_end, b_start, b_end):
    return not (a_end <= b_start or b_end <= a_start)


def calc_group_capacity(group: CourseGroup):
    course = group.course
    base = group.max_students_override if group.max_students_override else (course.max_students if course else 0)

    # если у курса лимит по аудитории и слот+аудитория определены — берём capacity аудитории
    if course and course.use_classroom_capacity and group.schedule_slot and group.schedule_slot.classroom:
        base = group.schedule_slot.classroom.capacity
    return base


@registration_bp.route("/enroll", methods=["POST"], strict_slashes=False)
def enroll_student():
    """
    Совместимость с UI:
    - принимает student_id + slot_id (как раньше)
    - сохраняет в CourseRegistration: preferred_slot_id=slot_id, group_id=slot.group_id, course_id=slot.group.course_id
    Дополнительно можно прислать:
    - level (1..10), comment, skills (array), status
    """
    data = request.json or {}
    student_id = data.get("student_id")
    slot_id = data.get("slot_id") or data.get("preferred_slot_id")

    course_id = data.get("course_id")
    category_id = data.get("category_id")
    group_id = data.get("group_id")
    block_id = data.get("block_id")

    if not student_id:
        return json_response({"error": "student_id is required"}, status=400)

    student = Student.query.get(student_id)
    if not student:
        return json_response({"error": "Student not found"}, status=404)

    preferred_slot = None
    if slot_id:
        preferred_slot = ScheduleSlot.query.get(slot_id)
        if not preferred_slot:
            return json_response({"error": "Slot not found"}, status=404)

        # слот однозначно => группа
        group_id = preferred_slot.group_id
        if preferred_slot.group:
            course_id = preferred_slot.group.course_id
            if category_id is None and preferred_slot.group.course:
                category_id = preferred_slot.group.course.category_id

    # если курс указали напрямую (без слота) — валидируем
    course = None
    if course_id is not None:
        course = Course.query.get(course_id)
        if not course:
            return json_response({"error": "course_id not found"}, status=400)
        if category_id is None:
            category_id = course.category_id

    # если указали направление — валидируем
    if category_id is not None and not CourseCategory.query.get(category_id):
        return json_response({"error": "category_id not found"}, status=400)

    # группа если пришла — валидируем
    group = None
    if group_id is not None:
        group = CourseGroup.query.get(group_id)
        if not group:
            return json_response({"error": "group_id not found"}, status=400)
        # если курс не задан — выведем из группы
        if course_id is None:
            course_id = group.course_id
            course = group.course
        # если слота нет — но есть группа — preferred_slot можно выставить из group.schedule_slot
        if preferred_slot is None and group.schedule_slot:
            preferred_slot = group.schedule_slot
            slot_id = preferred_slot.id

    # блок информатики если пришёл — валидируем
    if block_id is not None and not InformaticsBlock.query.get(block_id):
        return json_response({"error": "block_id not found"}, status=400)

    # требование: чтобы запись имела смысл, должен быть либо слот, либо курс, либо направление
    if not any([slot_id, course_id, category_id]):
        return json_response({"error": "Provide slot_id (preferred_slot_id) OR course_id OR category_id"}, status=400)

    # запрет повторно пройти тот же курс (когда course_id уже известен)
    if course_id is not None:
        exists = CourseRegistration.query.filter_by(student_id=student_id, course_id=course_id).first()
        if exists:
            return json_response({"error": "Student already has registration for this course"}, status=400)

    # запрет пересечения расписания ученика (если слот известен)
    if preferred_slot is not None:
        # ищем другие регистрации ученика, где уже назначена группа и есть слот
        other_regs = (
            CourseRegistration.query
            .filter(CourseRegistration.student_id == student_id)
            .filter(CourseRegistration.group_id.isnot(None))
            .all()
        )
        for r in other_regs:
            if r.group and r.group.schedule_slot:
                s = r.group.schedule_slot
                if s.day_of_week == preferred_slot.day_of_week and time_overlap(
                    preferred_slot.start_time, preferred_slot.end_time, s.start_time, s.end_time
                ):
                    return json_response({"error": "Student schedule conflict with another group"}, status=400)

    # проверка вместимости группы (если группа известна)
    if group is not None:
        capacity = calc_group_capacity(group)
        approved_count = CourseRegistration.query.filter_by(group_id=group.id, status="approved").count()
        if capacity and approved_count >= capacity:
            return json_response({"error": "Group is full"}, status=400)

    reg = CourseRegistration(
        student_id=student_id,
        course_id=course_id,
        category_id=category_id,
        group_id=group_id,
        preferred_slot_id=slot_id,
        block_id=block_id,
        comment=data.get("comment"),
        level=data.get("level"),
        skills=data.get("skills"),
        status=data.get("status", "approved"),
    )

    db.session.add(reg)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return json_response({"error": "IntegrityError", "details": str(e.orig)}, status=400)

    return json_response({
        "message": "Registration created",
        "registration": {
            "id": reg.id,
            "student_id": reg.student_id,
            "course_id": reg.course_id,
            "category_id": reg.category_id,
            "group_id": reg.group_id,
            "preferred_slot_id": reg.preferred_slot_id,
            "status": reg.status,
            "level": reg.level,
        }
    }, status=201)


@registration_bp.route("/filter_slots", methods=["GET"], strict_slashes=False)
def filter_slots():
    course_id = request.args.get("course_id", type=int)
    classroom = request.args.get("classroom")  # name
    day = request.args.get("day", type=int)
    academic_year = request.args.get("academic_year")

    q = ScheduleSlot.query.join(CourseGroup, ScheduleSlot.group_id == CourseGroup.id)

    if course_id:
        q = q.filter(CourseGroup.course_id == course_id)
    if academic_year:
        q = q.filter(CourseGroup.academic_year == academic_year)
    if day:
        q = q.filter(ScheduleSlot.day_of_week == day)
    if classroom:
        q = q.join(Classroom, ScheduleSlot.classroom_id == Classroom.id, isouter=True) \
             .filter(Classroom.name == classroom)

    slots = q.order_by(ScheduleSlot.id.asc()).all()
    return json_response([s.to_dict() for s in slots])


@registration_bp.route("/complete/<int:registration_id>", methods=["POST"], strict_slashes=False)
def complete_course(registration_id: int):
    reg = CourseRegistration.query.get(registration_id)
    if not reg:
        return json_response({"error": "Registration not found"}, status=404)

    reg.status = "completed"
    reg.completed_at = db.func.now()
    db.session.commit()
    return json_response({"message": "Course marked as completed"})

