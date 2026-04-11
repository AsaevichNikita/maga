from flask import Blueprint, Response, request
from sqlalchemy.exc import IntegrityError
import json

from src.app import db
from src.app.keycloak_auth import roles_required
from src.app.models import Assistant, Course, CourseGroup, InformaticsBlock, Teacher, parse_academic_year


course_groups_bp = Blueprint("course_groups", __name__)


def json_response(data, status=200):
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype="application/json; charset=utf-8",
        status=status,
    )


def group_to_dict(g: CourseGroup, with_assistants=True, with_slot=True):
    data = {
        "id": g.id,
        "course_id": g.course_id,
        "course_name": g.course.name if g.course else None,
        "name": g.name,
        "academic_year": g.academic_year,
        "academic_year_start": g.academic_year_start,
        "academic_year_end": g.academic_year_end,
        "is_active": g.is_active,
        "lead_teacher_id": g.lead_teacher_id,
        "lead_teacher": (
            f"{g.lead_teacher.lastname} {g.lead_teacher.firstname}" if g.lead_teacher else None
        ),
        "block_id": g.block_id,
        "block_name": g.informatics_block.name if g.informatics_block else None,
        "min_level": g.min_level,
        "max_level": g.max_level,
        "max_students_override": g.max_students_override,
        "created_at": g.created_at.isoformat() if g.created_at else None,
    }

    if with_assistants:
        data["assistants"] = [
            {
                "id": a.id,
                "firstname": a.firstname,
                "lastname": a.lastname,
                "phone_number": a.phone_number,
            }
            for a in (g.assistants or [])
        ]

    if with_slot:
        data["schedule_slot"] = g.schedule_slot.to_dict() if g.schedule_slot else None

    return data


def _validate_refs(course_id, lead_teacher_id=None, block_id=None):
    course = Course.query.get(course_id)
    if not course:
        return None, json_response({"error": "course_id not found"}, status=400)

    if lead_teacher_id is not None and not Teacher.query.get(lead_teacher_id):
        return None, json_response({"error": "lead_teacher_id not found"}, status=400)

    if block_id is not None:
        block = InformaticsBlock.query.get(block_id)
        if not block:
            return None, json_response({"error": "block_id not found"}, status=400)
        if block.course_id != course_id:
            return None, json_response({"error": "block_id does not belong to course_id"}, status=400)

    return course, None


@course_groups_bp.route("/", methods=["GET"], strict_slashes=False)
@roles_required("manager", "admin")
def groups_list():
    course_id = request.args.get("course_id", type=int)
    academic_year = request.args.get("academic_year")
    is_active = request.args.get("is_active", type=int)

    query = CourseGroup.query
    if course_id:
        query = query.filter(CourseGroup.course_id == course_id)
    if academic_year:
        try:
            start_year, end_year = parse_academic_year(academic_year)
        except ValueError as exc:
            return json_response({"error": str(exc)}, status=400)
        query = query.filter(
            CourseGroup.academic_year_start == start_year,
            CourseGroup.academic_year_end == end_year,
        )
    if is_active is not None:
        query = query.filter(CourseGroup.is_active == bool(is_active))

    items = query.order_by(CourseGroup.id.asc()).all()
    return json_response([group_to_dict(g) for g in items])


@course_groups_bp.route("/", methods=["POST"], strict_slashes=False)
@roles_required("manager", "admin")
def groups_create():
    data = request.json or {}
    course_id = data.get("course_id")
    name = data.get("name")
    academic_year = data.get("academic_year")

    if not all([course_id, name, academic_year]):
        return json_response({"error": "Missing required fields: course_id, name, academic_year"}, status=400)

    try:
        academic_year_start, academic_year_end = parse_academic_year(academic_year)
    except ValueError as exc:
        return json_response({"error": str(exc)}, status=400)

    lead_teacher_id = data.get("lead_teacher_id")
    block_id = data.get("block_id")

    _, error_response = _validate_refs(course_id, lead_teacher_id=lead_teacher_id, block_id=block_id)
    if error_response:
        return error_response

    group = CourseGroup(
        course_id=course_id,
        name=name,
        academic_year_start=academic_year_start,
        academic_year_end=academic_year_end,
        is_active=bool(data.get("is_active", True)),
        lead_teacher_id=lead_teacher_id,
        block_id=block_id,
        min_level=data.get("min_level"),
        max_level=data.get("max_level"),
        max_students_override=data.get("max_students_override"),
    )

    assistant_ids = data.get("assistant_ids") or []
    if assistant_ids:
        assistants = Assistant.query.filter(Assistant.id.in_(assistant_ids)).all()
        if len(assistants) != len(set(assistant_ids)):
            return json_response({"error": "Some assistants not found in assistant_ids"}, status=400)
        group.assistants = assistants

    db.session.add(group)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return json_response({"error": "IntegrityError", "details": str(e.orig)}, status=400)

    return json_response(group_to_dict(group), status=201)


@course_groups_bp.route("/<int:group_id>", methods=["GET"], strict_slashes=False)
@roles_required("manager", "admin")
def group_get(group_id: int):
    group = CourseGroup.query.get(group_id)
    if not group:
        return json_response({"error": "CourseGroup not found"}, status=404)
    return json_response(group_to_dict(group, with_assistants=True, with_slot=True))


@course_groups_bp.route("/<int:group_id>", methods=["PUT"], strict_slashes=False)
@roles_required("manager", "admin")
def group_update(group_id: int):
    group = CourseGroup.query.get(group_id)
    if not group:
        return json_response({"error": "CourseGroup not found"}, status=404)

    data = request.json or {}

    if "course_id" in data:
        course_id = data["course_id"]
        _, error_response = _validate_refs(
            course_id,
            lead_teacher_id=data.get("lead_teacher_id", group.lead_teacher_id),
            block_id=data.get("block_id", group.block_id),
        )
        if error_response:
            return error_response
        group.course_id = course_id

    if "name" in data:
        group.name = data["name"]
    if "academic_year" in data:
        try:
            start_year, end_year = parse_academic_year(data["academic_year"])
        except ValueError as exc:
            return json_response({"error": str(exc)}, status=400)
        group.academic_year_start = start_year
        group.academic_year_end = end_year
    if "is_active" in data:
        group.is_active = bool(data["is_active"])
    if "min_level" in data:
        group.min_level = data["min_level"]
    if "max_level" in data:
        group.max_level = data["max_level"]
    if "max_students_override" in data:
        group.max_students_override = data["max_students_override"]

    if "lead_teacher_id" in data:
        teacher_id = data["lead_teacher_id"]
        if teacher_id is not None and not Teacher.query.get(teacher_id):
            return json_response({"error": "lead_teacher_id not found"}, status=400)
        group.lead_teacher_id = teacher_id

    if "block_id" in data:
        block_id = data["block_id"]
        if block_id is not None:
            block = InformaticsBlock.query.get(block_id)
            if not block:
                return json_response({"error": "block_id not found"}, status=400)
            if block.course_id != group.course_id:
                return json_response({"error": "block_id does not belong to group.course_id"}, status=400)
        group.block_id = block_id

    if "assistant_ids" in data:
        ids = data["assistant_ids"] or []
        assistants = Assistant.query.filter(Assistant.id.in_(ids)).all() if ids else []
        if len(assistants) != len(set(ids)):
            return json_response({"error": "Some assistants not found in assistant_ids"}, status=400)
        group.assistants = assistants

    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return json_response({"error": "IntegrityError", "details": str(e.orig)}, status=400)

    return json_response(group_to_dict(group, with_assistants=True, with_slot=True))


@course_groups_bp.route("/<int:group_id>", methods=["DELETE"], strict_slashes=False)
@roles_required("admin")
def group_delete(group_id: int):
    group = CourseGroup.query.get(group_id)
    if not group:
        return json_response({"error": "CourseGroup not found"}, status=404)

    db.session.delete(group)
    db.session.commit()
    return json_response({"message": "Deleted successfully"})


@course_groups_bp.route("/<int:group_id>/assistants", methods=["GET"], strict_slashes=False)
@roles_required("manager", "admin")
def group_assistants_get(group_id: int):
    group = CourseGroup.query.get(group_id)
    if not group:
        return json_response({"error": "CourseGroup not found"}, status=404)

    return json_response([
        {"id": a.id, "firstname": a.firstname, "lastname": a.lastname, "phone_number": a.phone_number}
        for a in (group.assistants or [])
    ])


@course_groups_bp.route("/<int:group_id>/assistants", methods=["PUT"], strict_slashes=False)
@roles_required("manager", "admin")
def group_assistants_update(group_id: int):
    group = CourseGroup.query.get(group_id)
    if not group:
        return json_response({"error": "CourseGroup not found"}, status=404)

    data = request.json or {}
    ids = data.get("assistant_ids", [])
    assistants = Assistant.query.filter(Assistant.id.in_(ids)).all() if ids else []
    if len(assistants) != len(set(ids)):
        return json_response({"error": "Some assistants not found in assistant_ids"}, status=400)

    group.assistants = assistants
    db.session.commit()
    return json_response({"message": "Updated", "assistant_ids": ids})
