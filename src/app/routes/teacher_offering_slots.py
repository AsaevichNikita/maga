from flask import Blueprint, request, Response
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import json

from src.app import db
from src.app.current_user import get_current_teacher
from src.app.keycloak_auth import roles_required
from src.app.models import TeacherOfferingSlot, Teacher, Course, Classroom


teacher_offering_slots_bp = Blueprint("teacher_offering_slots", __name__)


def json_response(data, status=200):
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype='application/json; charset=utf-8',
        status=status
    )


def slot_to_dict(s: TeacherOfferingSlot):
    return {
        "id": s.id,
        "teacher_id": s.teacher_id,
        "teacher_name": (
            f"{s.teacher.lastname} {s.teacher.firstname} {s.teacher.surname or ''}".strip()
            if s.teacher else None
        ),
        "course_id": s.course_id,
        "course_name": s.course.name if s.course else None,
        "academic_year": s.academic_year,
        "day_of_week": s.day_of_week,
        "start_time": s.start_time.strftime("%H:%M") if s.start_time else None,
        "end_time": s.end_time.strftime("%H:%M") if s.end_time else None,
        "classroom_id": s.classroom_id,
        "classroom_name": s.classroom.name if s.classroom else None,
        "classroom_capacity": s.classroom.capacity if s.classroom else None,
        "is_active": s.is_active,
        "max_groups": s.max_groups,
        "priority": s.priority,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


@teacher_offering_slots_bp.route("/my", methods=["GET"], strict_slashes=False)
@roles_required("teacher", "admin")
def my_teacher_offering_slots():
    teacher = get_current_teacher()
    if not teacher:
        return json_response({"error": "Teacher profile is not linked to current Keycloak user"}, status=404)

    academic_year = request.args.get("academic_year")
    is_active = request.args.get("is_active", type=int)

    q = TeacherOfferingSlot.query.filter_by(teacher_id=teacher.id)

    if is_active is not None:
        q = q.filter(TeacherOfferingSlot.is_active == bool(is_active))

    if academic_year:
        try:
            start_year, end_year = academic_year.replace("-", "/").split("/")
            q = q.filter(
                TeacherOfferingSlot.academic_year_start == int(start_year),
                TeacherOfferingSlot.academic_year_end == int(end_year),
            )
        except ValueError:
            return json_response(
                {"error": "academic_year must be in format YYYY/YYYY or YYYY-YYYY"},
                status=400
            )

    items = q.order_by(
        TeacherOfferingSlot.academic_year_start.asc(),
        TeacherOfferingSlot.day_of_week.asc(),
        TeacherOfferingSlot.start_time.asc(),
        TeacherOfferingSlot.id.asc()
    ).all()

    return json_response([slot_to_dict(x) for x in items])


@teacher_offering_slots_bp.route("/", methods=["GET"], strict_slashes=False)
def list_teacher_offering_slots():
    teacher_id = request.args.get("teacher_id", type=int)
    course_id = request.args.get("course_id", type=int)
    academic_year = request.args.get("academic_year")
    is_active = request.args.get("is_active", type=int)

    q = TeacherOfferingSlot.query.filter(TeacherOfferingSlot.is_active == True)

    if teacher_id:
        q = q.filter(TeacherOfferingSlot.teacher_id == teacher_id)
    if course_id:
        q = q.filter(TeacherOfferingSlot.course_id == course_id)
    if is_active is not None:
        q = q.filter(TeacherOfferingSlot.is_active == bool(is_active))

    if academic_year:
        try:
            start_year, end_year = academic_year.replace("-", "/").split("/")
            q = q.filter(
                TeacherOfferingSlot.academic_year_start == int(start_year),
                TeacherOfferingSlot.academic_year_end == int(end_year),
            )
        except ValueError:
            return json_response(
                {"error": "academic_year must be in format YYYY/YYYY or YYYY-YYYY"},
                status=400
            )

    items = q.order_by(
        TeacherOfferingSlot.academic_year_start.asc(),
        TeacherOfferingSlot.day_of_week.asc(),
        TeacherOfferingSlot.start_time.asc(),
        TeacherOfferingSlot.id.asc()
    ).all()

    return json_response([slot_to_dict(x) for x in items])


@teacher_offering_slots_bp.route("/", methods=["POST"], strict_slashes=False)
@roles_required("manager", "admin")
def create_teacher_offering_slot():
    data = request.json or {}

    teacher_id = data.get("teacher_id")
    course_id = data.get("course_id")
    academic_year = data.get("academic_year")
    day_of_week = data.get("day_of_week")
    start_time_str = data.get("start_time")
    end_time_str = data.get("end_time")

    required = ["teacher_id", "course_id", "academic_year", "day_of_week", "start_time", "end_time"]
    missing = [x for x in required if not data.get(x)]
    if missing:
        return json_response(
            {"error": f"Missing required fields: {', '.join(missing)}"},
            status=400
        )

    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        return json_response({"error": "teacher_id not found"}, status=400)

    course = Course.query.get(course_id)
    if not course:
        return json_response({"error": "course_id not found"}, status=400)

    try:
        day_of_week = int(day_of_week)
    except (TypeError, ValueError):
        return json_response({"error": "day_of_week must be an integer"}, status=400)

    if day_of_week < 1 or day_of_week > 7:
        return json_response({"error": "day_of_week must be between 1 and 7"}, status=400)

    try:
        start_time = datetime.strptime(start_time_str, "%H:%M").time()
        end_time = datetime.strptime(end_time_str, "%H:%M").time()
    except ValueError:
        return json_response({"error": "start_time/end_time must be HH:MM"}, status=400)

    classroom_id = data.get("classroom_id")
    classroom = None
    if classroom_id is not None:
        classroom = Classroom.query.get(classroom_id)
        if not classroom:
            return json_response({"error": "classroom_id not found"}, status=400)

    try:
        start_year, end_year = academic_year.replace("-", "/").split("/")
        start_year = int(start_year)
        end_year = int(end_year)
    except ValueError:
        return json_response(
            {"error": "academic_year must be in format YYYY/YYYY or YYYY-YYYY"},
            status=400
        )

    if end_year != start_year + 1:
        return json_response(
            {"error": "academic_year_end must equal academic_year_start + 1"},
            status=400
        )

    slot = TeacherOfferingSlot(
        teacher_id=teacher_id,
        course_id=course_id,
        academic_year_start=start_year,
        academic_year_end=end_year,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        classroom_id=classroom.id if classroom else None,
        is_active=bool(data.get("is_active", True)),
        max_groups=int(data.get("max_groups", 1)),
        priority=int(data.get("priority", 100)),
    )

    db.session.add(slot)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return json_response({"error": "IntegrityError", "details": str(e.orig)}, status=400)

    return json_response(slot_to_dict(slot), status=201)


@teacher_offering_slots_bp.route("/<int:slot_id>", methods=["GET"], strict_slashes=False)
def get_teacher_offering_slot(slot_id: int):
    slot = TeacherOfferingSlot.query.get(slot_id)
    if not slot:
        return json_response({"error": "TeacherOfferingSlot not found"}, status=404)

    return json_response(slot_to_dict(slot))


@teacher_offering_slots_bp.route("/<int:slot_id>", methods=["PUT"], strict_slashes=False)
@roles_required("manager", "admin")
def update_teacher_offering_slot(slot_id: int):
    slot = TeacherOfferingSlot.query.get(slot_id)
    if not slot:
        return json_response({"error": "TeacherOfferingSlot not found"}, status=404)

    data = request.json or {}

    if "teacher_id" in data:
        teacher_id = data["teacher_id"]
        teacher = Teacher.query.get(teacher_id)
        if not teacher:
            return json_response({"error": "teacher_id not found"}, status=400)
        slot.teacher_id = teacher_id

    if "course_id" in data:
        course_id = data["course_id"]
        course = Course.query.get(course_id)
        if not course:
            return json_response({"error": "course_id not found"}, status=400)
        slot.course_id = course_id

    if "academic_year" in data:
        academic_year = data["academic_year"]
        try:
            start_year, end_year = academic_year.replace("-", "/").split("/")
            start_year = int(start_year)
            end_year = int(end_year)
        except ValueError:
            return json_response(
                {"error": "academic_year must be in format YYYY/YYYY or YYYY-YYYY"},
                status=400
            )
        if end_year != start_year + 1:
            return json_response(
                {"error": "academic_year_end must equal academic_year_start + 1"},
                status=400
            )
        slot.academic_year_start = start_year
        slot.academic_year_end = end_year

    if "day_of_week" in data:
        try:
            day_of_week = int(data["day_of_week"])
        except (TypeError, ValueError):
            return json_response({"error": "day_of_week must be an integer"}, status=400)
        if day_of_week < 1 or day_of_week > 7:
            return json_response({"error": "day_of_week must be between 1 and 7"}, status=400)
        slot.day_of_week = day_of_week

    if "start_time" in data:
        try:
            slot.start_time = datetime.strptime(data["start_time"], "%H:%M").time()
        except ValueError:
            return json_response({"error": "start_time must be HH:MM"}, status=400)

    if "end_time" in data:
        try:
            slot.end_time = datetime.strptime(data["end_time"], "%H:%M").time()
        except ValueError:
            return json_response({"error": "end_time must be HH:MM"}, status=400)

    if "classroom_id" in data:
        classroom_id = data["classroom_id"]
        if classroom_id is None:
            slot.classroom_id = None
        else:
            classroom = Classroom.query.get(classroom_id)
            if not classroom:
                return json_response({"error": "classroom_id not found"}, status=400)
            slot.classroom_id = classroom.id

    if "is_active" in data:
        slot.is_active = bool(data["is_active"])

    if "max_groups" in data:
        slot.max_groups = int(data["max_groups"])

    if "priority" in data:
        slot.priority = int(data["priority"])

    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return json_response({"error": "IntegrityError", "details": str(e.orig)}, status=400)

    return json_response(slot_to_dict(slot))


@teacher_offering_slots_bp.route("/<int:slot_id>", methods=["DELETE"], strict_slashes=False)
@roles_required("admin")
def delete_teacher_offering_slot(slot_id: int):
    slot = TeacherOfferingSlot.query.get(slot_id)
    if not slot:
        return json_response({"error": "TeacherOfferingSlot not found"}, status=404)

    db.session.delete(slot)
    db.session.commit()
    return json_response({"message": "Deleted successfully"})