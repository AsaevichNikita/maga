from flask import Blueprint, request, Response
from sqlalchemy.exc import IntegrityError
import json

from src.app import db
from src.app.keycloak_auth import roles_required
from src.app.models import CourseCategory


course_categories_bp = Blueprint("course_categories", __name__)


def json_response(data, status=200):
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype="application/json; charset=utf-8",
        status=status
    )


def category_to_dict(c: CourseCategory):
    return {
        "id": c.id,
        "name": c.name,
        "description": c.description,
        "min_grade": c.min_grade,
        "max_grade": c.max_grade,
        "min_age": c.min_age,
        "max_age": c.max_age,
        "education_level": c.education_level,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


@course_categories_bp.route("/", methods=["GET"], strict_slashes=False)
def categories_list():
    items = CourseCategory.query.order_by(CourseCategory.id.asc()).all()
    return json_response([category_to_dict(x) for x in items])


@course_categories_bp.route("/", methods=["POST"], strict_slashes=False)
@roles_required("manager", "admin")
def categories_create():
    data = request.json or {}
    name = data.get("name")
    if not name:
        return json_response({"error": "Missing required field: name"}, status=400)

    c = CourseCategory(
        name=name,
        description=data.get("description"),
        min_grade=data.get("min_grade"),
        max_grade=data.get("max_grade"),
        min_age=data.get("min_age"),
        max_age=data.get("max_age"),
        education_level=data.get("education_level"),
    )
    db.session.add(c)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return json_response({"error": "IntegrityError", "details": str(e.orig)}, status=400)

    return json_response(category_to_dict(c), status=201)


@course_categories_bp.route("/<int:category_id>", methods=["GET"], strict_slashes=False)
def category_get(category_id: int):
    c = CourseCategory.query.get(category_id)
    if not c:
        return json_response({"error": "CourseCategory not found"}, status=404)

    return json_response(category_to_dict(c))


@course_categories_bp.route("/<int:category_id>", methods=["PUT"], strict_slashes=False)
@roles_required("manager", "admin")
def category_update(category_id: int):
    c = CourseCategory.query.get(category_id)
    if not c:
        return json_response({"error": "CourseCategory not found"}, status=404)

    data = request.json or {}
    for k in ["name", "description", "min_grade", "max_grade", "min_age", "max_age", "education_level"]:
        if k in data:
            setattr(c, k, data[k])

    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return json_response({"error": "IntegrityError", "details": str(e.orig)}, status=400)

    return json_response(category_to_dict(c))


@course_categories_bp.route("/<int:category_id>", methods=["DELETE"], strict_slashes=False)
@roles_required("admin")
def category_delete(category_id: int):
    c = CourseCategory.query.get(category_id)
    if not c:
        return json_response({"error": "CourseCategory not found"}, status=404)

    db.session.delete(c)
    db.session.commit()
    return json_response({"message": "Deleted successfully"})