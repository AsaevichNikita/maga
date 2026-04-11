from flask import Blueprint, request, Response, jsonify
from sqlalchemy.exc import IntegrityError
import json

from src.app import db
from src.app.keycloak_auth import roles_required
from src.app.models import Course, CourseCategory, Teacher, CourseGroup, course_teachers, CourseRegistration, ScheduleSlot


courses_bp = Blueprint("courses", __name__)


def json_response(data, status=200):
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype="application/json; charset=utf-8",
        status=status
    )


def teacher_short(t: Teacher):
    return {
        "id": t.id,
        "firstname": t.firstname,
        "lastname": t.lastname,
        "surname": t.surname,
        "email": t.email
    }


def course_to_dict(c: Course, with_teachers=False, with_groups=False):
    d = {
        "id": c.id,
        "name": c.name,
        "description": c.description,
        "category_id": c.category_id,
        "category": c.category.name if c.category else None,
        "max_students": c.max_students,
        "use_classroom_capacity": c.use_classroom_capacity,
        "duration_minutes": c.duration_minutes,
        "price": float(c.price) if c.price is not None else None,
        "is_active": c.is_active,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }
    if with_teachers:
        d["allowed_teachers"] = [teacher_short(t) for t in (c.allowed_teachers or [])]
    if with_groups:
        d["groups"] = [
            {"id": g.id, "name": g.name, "academic_year": g.academic_year, "is_active": g.is_active}
            for g in (c.groups or [])
        ]
    return d


@courses_bp.route("/", methods=["GET"], strict_slashes=False)
def courses_list():
    category_id = request.args.get("category_id", type=int)
    is_active = request.args.get("is_active", type=int)
    teacher_id = request.args.get("teacher_id", type=int)

    q = Course.query
    if category_id:
        q = q.filter(Course.category_id == category_id)
    if is_active is not None:
        q = q.filter(Course.is_active == bool(is_active))
    if teacher_id:
        q = q.join(course_teachers, Course.id == course_teachers.c.course_id) \
             .filter(course_teachers.c.teacher_id == teacher_id)

    items = q.order_by(Course.id.asc()).all()
    return json_response([course_to_dict(c, with_teachers=True) for c in items])


@courses_bp.route("/", methods=["POST"], strict_slashes=False)
@roles_required("manager", "admin")
def courses_create():
    data = request.json or {}
    name = data.get("name")
    if not name:
        return json_response({"error": "Missing required field: name"}, status=400)

    category_id = data.get("category_id")
    if category_id is not None and not CourseCategory.query.get(category_id):
        return json_response({"error": "category_id not found"}, status=400)

    c = Course(
        name=name,
        description=data.get("description"),
        category_id=category_id,
        max_students=data.get("max_students", 15),
        use_classroom_capacity=bool(data.get("use_classroom_capacity", False)),
        duration_minutes=data.get("duration_minutes", 90),
        price=data.get("price"),
        is_active=bool(data.get("is_active", True)),
    )

    allowed_teacher_ids = data.get("allowed_teacher_ids")
    teacher_id = data.get("teacher_id")
    if allowed_teacher_ids is None and teacher_id is not None:
        allowed_teacher_ids = [teacher_id]

    if allowed_teacher_ids:
        teachers = Teacher.query.filter(Teacher.id.in_(allowed_teacher_ids)).all()
        if len(teachers) != len(set(allowed_teacher_ids)):
            return json_response({"error": "Some teachers not found in allowed_teacher_ids"}, status=400)
        c.allowed_teachers = teachers

    db.session.add(c)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return json_response({"error": "IntegrityError", "details": str(e.orig)}, status=400)

    return json_response(course_to_dict(c, with_teachers=True), status=201)


@courses_bp.route("/<int:course_id>", methods=["GET"], strict_slashes=False)
def course_get(course_id: int):
    c = Course.query.get(course_id)
    if not c:
        return json_response({"error": "Course not found"}, status=404)

    return json_response(course_to_dict(c, with_teachers=True, with_groups=True))


@courses_bp.route("/<int:course_id>", methods=["PUT"], strict_slashes=False)
@roles_required("manager", "admin")
def course_update(course_id: int):
    c = Course.query.get(course_id)
    if not c:
        return json_response({"error": "Course not found"}, status=404)

    data = request.json or {}
    for k in ["name", "description", "max_students", "use_classroom_capacity", "duration_minutes", "price", "is_active"]:
        if k in data:
            setattr(c, k, data[k])

    if "category_id" in data:
        category_id = data["category_id"]
        if category_id is not None and not CourseCategory.query.get(category_id):
            return json_response({"error": "category_id not found"}, status=400)
        c.category_id = category_id

    if "allowed_teacher_ids" in data:
        ids = data["allowed_teacher_ids"] or []
        teachers = Teacher.query.filter(Teacher.id.in_(ids)).all() if ids else []
        if len(teachers) != len(set(ids)):
            return json_response({"error": "Some teachers not found in allowed_teacher_ids"}, status=400)
        c.allowed_teachers = teachers

    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return json_response({"error": "IntegrityError", "details": str(e.orig)}, status=400)

    return json_response(course_to_dict(c, with_teachers=True, with_groups=True))


@courses_bp.route("/<int:course_id>", methods=["DELETE"], strict_slashes=False)
@roles_required("admin")
def course_delete(course_id: int):
    c = Course.query.get(course_id)
    if not c:
        return json_response({"error": "Course not found"}, status=404)

    db.session.delete(c)
    db.session.commit()
    return json_response({"message": "Deleted successfully"})


@courses_bp.route("/<int:course_id>/teachers", methods=["GET"], strict_slashes=False)
@roles_required("manager", "admin")
def course_teachers_get(course_id: int):
    c = Course.query.get(course_id)
    if not c:
        return json_response({"error": "Course not found"}, status=404)

    return json_response([teacher_short(t) for t in (c.allowed_teachers or [])])


@courses_bp.route("/<int:course_id>/teachers", methods=["PUT"], strict_slashes=False)
@roles_required("manager", "admin")
def course_teachers_put(course_id: int):
    c = Course.query.get(course_id)
    if not c:
        return json_response({"error": "Course not found"}, status=404)

    data = request.json or {}
    ids = data.get("allowed_teacher_ids", [])
    teachers = Teacher.query.filter(Teacher.id.in_(ids)).all() if ids else []
    if len(teachers) != len(set(ids)):
        return json_response({"error": "Some teachers not found in allowed_teacher_ids"}, status=400)

    c.allowed_teachers = teachers
    db.session.commit()
    return json_response({"message": "Updated", "allowed_teachers": [teacher_short(t) for t in teachers]})


@courses_bp.get("/<int:course_id>/students")
@roles_required("manager", "admin")
def course_students(course_id: int):
    course = Course.query.get(course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    regs = (
        CourseRegistration.query
        .filter(CourseRegistration.course_id == course_id)
        .order_by(CourseRegistration.id.asc())
        .all()
    )

    result = []
    for r in regs:
        s = r.student
        if not s:
            continue
        result.append({
            "registration_id": r.id,
            "status": r.status,
            "level": r.level,
            "student": {
                "id": s.id,
                "firstname": s.firstname,
                "lastname": s.lastname,
                "surname": s.surname,
                "phone_number": s.phone_number,
                "email": s.email,
                "birthday": s.birthday.isoformat() if s.birthday else None,
                "education_type": s.education_type,
                "group_name": s.group_name,
            }
        })

    return jsonify(result), 200


@courses_bp.get("/<int:course_id>/slots")
def course_slots(course_id: int):
    course = Course.query.get(course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    slots = (
        ScheduleSlot.query
        .join(CourseGroup, ScheduleSlot.group_id == CourseGroup.id)
        .filter(CourseGroup.course_id == course_id)
        .order_by(ScheduleSlot.day_of_week.asc(), ScheduleSlot.start_time.asc())
        .all()
    )

    return jsonify([s.to_dict() for s in slots]), 200