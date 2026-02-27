from flask import Blueprint, request, Response
from sqlalchemy.exc import IntegrityError
import json

from src.app import db
from src.app.models import Classroom


classrooms_bp = Blueprint("classrooms", __name__, url_prefix="/classrooms")


def json_response(data, status=200):
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype="application/json; charset=utf-8",
        status=status
    )


def classroom_to_dict(c: Classroom):
    return {"id": c.id, "name": c.name, "capacity": c.capacity}


@classrooms_bp.route("/", methods=["GET", "POST"], strict_slashes=False)
def classrooms_list_create():
    if request.method == "GET":
        items = Classroom.query.order_by(Classroom.id.asc()).all()
        return json_response([classroom_to_dict(x) for x in items])

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


@classrooms_bp.route("/<int:classroom_id>", methods=["GET", "PUT", "DELETE"], strict_slashes=False)
def classroom_detail(classroom_id: int):
    c = Classroom.query.get(classroom_id)
    if not c:
        return json_response({"error": "Classroom not found"}, status=404)

    if request.method == "GET":
        return json_response(classroom_to_dict(c))

    if request.method == "PUT":
        data = request.json or {}
        if "name" in data: c.name = data["name"]
        if "capacity" in data: c.capacity = data["capacity"]
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            return json_response({"error": "IntegrityError", "details": str(e.orig)}, status=400)
        return json_response(classroom_to_dict(c))

    db.session.delete(c)
    db.session.commit()
    return json_response({"message": "Deleted successfully"})