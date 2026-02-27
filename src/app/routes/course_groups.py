from flask import Blueprint, request, Response
from sqlalchemy.exc import IntegrityError
import json

from src.app import db
from src.app.models import CourseGroup, Course, Teacher, Assistant


course_groups_bp = Blueprint("course_groups", __name__, url_prefix="/course-groups")


def json_response(data, status=200):
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype="application/json; charset=utf-8",
        status=status
    )


def group_to_dict(g: CourseGroup, with_assistants=True, with_slot=True):
    d = {
        "id": g.id,
        "course_id": g.course_id,
        "course_name": g.course.name if g.course else None,
        "name": g.name,
        "academic_year": g.academic_year,
        "is_active": g.is_active,
        "lead_teacher_id": g.lead_teacher_id,
        "lead_teacher": (
            f"{g.lead_teacher.lastname} {g.lead_teacher.firstname}"
            if g.lead_teacher else None
        ),
        "block_id": g.block_id,
        "min_level": g.min_level,
        "max_level": g.max_level,
        "max_students_override": g.max_students_override,
        "created_at": g.created_at.isoformat() if g.created_at else None,
    }

    if with_assistants:
        d["assistants"] = [
            {
                "id": a.id,
                "firstname": a.firstname,
                "lastname": a.lastname,
                "phone_number": a.phone_number
            } for a in (g.assistants or [])
        ]

    if with_slot:
        d["schedule_slot"] = g.schedule_slot.to_dict() if g.schedule_slot else None

    return d


@course_groups_bp.route("/", methods=["GET", "POST"], strict_slashes=False)
def groups_list_create():
    if request.method == "GET":
        course_id = request.args.get("course_id", type=int)
        academic_year = request.args.get("academic_year")
        is_active = request.args.get("is_active", type=int)

        q = CourseGroup.query
        if course_id:
            q = q.filter(CourseGroup.course_id == course_id)
        if academic_year:
            q = q.filter(CourseGroup.academic_year == academic_year)
        if is_active is not None:
            q = q.filter(CourseGroup.is_active == bool(is_active))

        items = q.order_by(CourseGroup.id.asc()).all()
        return json_response([group_to_dict(g) for g in items])

    data = request.json or {}
    course_id = data.get("course_id")
    name = data.get("name")
    academic_year = data.get("academic_year")

    if not all([course_id, name, academic_year]):
        return json_response({"error": "Missing required fields: course_id, name, academic_year"}, status=400)

    course = Course.query.get(course_id)
    if not course:
        return json_response({"error": "course_id not found"}, status=400)

    lead_teacher_id = data.get("lead_teacher_id")
    if lead_teacher_id is not None and not Teacher.query.get(lead_teacher_id):
        return json_response({"error": "lead_teacher_id not found"}, status=400)

    g = CourseGroup(
        course_id=course_id,
        name=name,
        academic_year=academic_year,
        is_active=bool(data.get("is_active", True)),
        lead_teacher_id=lead_teacher_id,
        block_id=data.get("block_id"),
        min_level=data.get("min_level"),
        max_level=data.get("max_level"),
        max_students_override=data.get("max_students_override"),
    )

    assistant_ids = data.get("assistant_ids") or []
    if assistant_ids:
        assistants = Assistant.query.filter(Assistant.id.in_(assistant_ids)).all()
        if len(assistants) != len(set(assistant_ids)):
            return json_response({"error": "Some assistants not found in assistant_ids"}, status=400)
        g.assistants = assistants

    db.session.add(g)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return json_response({"error": "IntegrityError", "details": str(e.orig)}, status=400)

    return json_response(group_to_dict(g), status=201)


@course_groups_bp.route("/<int:group_id>", methods=["GET", "PUT", "DELETE"], strict_slashes=False)
def group_detail(group_id: int):
    g = CourseGroup.query.get(group_id)
    if not g:
        return json_response({"error": "CourseGroup not found"}, status=404)

    if request.method == "GET":
        return json_response(group_to_dict(g, with_assistants=True, with_slot=True))

    if request.method == "PUT":
        data = request.json or {}

        if "name" in data: g.name = data["name"]
        if "academic_year" in data: g.academic_year = data["academic_year"]
        if "is_active" in data: g.is_active = bool(data["is_active"])
        if "min_level" in data: g.min_level = data["min_level"]
        if "max_level" in data: g.max_level = data["max_level"]
        if "max_students_override" in data: g.max_students_override = data["max_students_override"]
        if "block_id" in data: g.block_id = data["block_id"]

        if "lead_teacher_id" in data:
            v = data["lead_teacher_id"]
            if v is not None and not Teacher.query.get(v):
                return json_response({"error": "lead_teacher_id not found"}, status=400)
            g.lead_teacher_id = v

        if "assistant_ids" in data:
            ids = data["assistant_ids"] or []
            assistants = Assistant.query.filter(Assistant.id.in_(ids)).all() if ids else []
            if len(assistants) != len(set(ids)):
                return json_response({"error": "Some assistants not found in assistant_ids"}, status=400)
            g.assistants = assistants

        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            return json_response({"error": "IntegrityError", "details": str(e.orig)}, status=400)

        return json_response(group_to_dict(g, with_assistants=True, with_slot=True))

    db.session.delete(g)
    db.session.commit()
    return json_response({"message": "Deleted successfully"})


@course_groups_bp.route("/<int:group_id>/assistants", methods=["GET", "PUT"], strict_slashes=False)
def group_assistants_api(group_id: int):
    g = CourseGroup.query.get(group_id)
    if not g:
        return json_response({"error": "CourseGroup not found"}, status=404)

    if request.method == "GET":
        return json_response([
            {"id": a.id, "firstname": a.firstname, "lastname": a.lastname, "phone_number": a.phone_number}
            for a in (g.assistants or [])
        ])

    data = request.json or {}
    ids = data.get("assistant_ids", [])
    assistants = Assistant.query.filter(Assistant.id.in_(ids)).all() if ids else []
    if len(assistants) != len(set(ids)):
        return json_response({"error": "Some assistants not found in assistant_ids"}, status=400)

    g.assistants = assistants
    db.session.commit()
    return json_response({"message": "Updated", "assistant_ids": ids})