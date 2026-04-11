from flask import Blueprint, Response, request
from sqlalchemy.exc import IntegrityError
import json

from src.app import db
from src.app.keycloak_auth import roles_required
from src.app.models import Classroom


classrooms_bp = Blueprint("classrooms", __name__)


def json_response(data, status=200):
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype="application/json; charset=utf-8",
        status=status,
    )


def classroom_to_dict(c: Classroom):
    return {"id": c.id, "name": c.name, "capacity": c.capacity}


@classrooms_bp.route("/", methods=["GET"], strict_slashes=False)
@roles_required("manager", "admin")
def classrooms_list():
    items = Classroom.query.order_by(Classroom.id.asc()).all()
    return json_response([classroom_to_dict(x) for x in items])


@classrooms_bp.route("/", methods=["POST"], strict_slashes=False)
@roles_required("manager", "admin")
def classrooms_create():
    data = request.json or {}
    name = data.get("name")
    if not name:
        return json_response({"error": "Missing required field: name"}, status=400)

    c = Classroom(name=name, capacity=data.get("capacity", 15))
    db.session.add(c)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return json_response({"error": "IntegrityError", "details": str(e.orig)}, status=400)

    return json_response(classroom_to_dict(c), status=201)


@classrooms_bp.route("/<int:classroom_id>", methods=["GET"], strict_slashes=False)
@roles_required("manager", "admin")
def classroom_get(classroom_id: int):
    c = Classroom.query.get(classroom_id)
    if not c:
        return json_response({"error": "Classroom not found"}, status=404)
    return json_response(classroom_to_dict(c))


@classrooms_bp.route("/<int:classroom_id>", methods=["PUT"], strict_slashes=False)
@roles_required("manager", "admin")
def classroom_update(classroom_id: int):
    c = Classroom.query.get(classroom_id)
    if not c:
        return json_response({"error": "Classroom not found"}, status=404)

    data = request.json or {}
    if "name" in data:
        c.name = data["name"]
    if "capacity" in data:
        c.capacity = data["capacity"]

    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return json_response({"error": "IntegrityError", "details": str(e.orig)}, status=400)

    return json_response(classroom_to_dict(c))


@classrooms_bp.route("/<int:classroom_id>", methods=["DELETE"], strict_slashes=False)
@roles_required("admin")
def classroom_delete(classroom_id: int):
    c = Classroom.query.get(classroom_id)
    if not c:
        return json_response({"error": "Classroom not found"}, status=404)

    db.session.delete(c)
    db.session.commit()
    return json_response({"message": "Deleted successfully"})
