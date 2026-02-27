from flask import Blueprint, request, Response
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import json

from src.app import db
from src.app.models import Assistant, CourseGroup


assistants_bp = Blueprint("assistants", __name__, url_prefix="/assistants")


def json_response(data, status=200):
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype="application/json; charset=utf-8",
        status=status
    )


def assistant_to_dict(a: Assistant, with_groups: bool = False):
    d = {
        "id": a.id,
        "firstname": a.firstname,
        "lastname": a.lastname,
        "surname": a.surname,
        "birthday": a.birthday.isoformat() if a.birthday else None,
        "phone_number": a.phone_number,
        "email": a.email,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }
    if with_groups:
        d["groups"] = [
            {
                "id": g.id,
                "name": g.name,
                "academic_year": g.academic_year,
                "course_id": g.course_id,
            } for g in (a.groups or [])
        ]
    return d


@assistants_bp.route("/", methods=["GET", "POST"], strict_slashes=False)
def assistants_list_create():
    if request.method == "GET":
        with_groups = request.args.get("with_groups", "0") == "1"
        items = Assistant.query.order_by(Assistant.id.asc()).all()
        return json_response([assistant_to_dict(a, with_groups=with_groups) for a in items])

    data = request.json or {}
    firstname = data.get("firstname")
    lastname = data.get("lastname")
    birthday_str = data.get("birthday")
    phone_number = data.get("phone_number")

    if not all([firstname, lastname, birthday_str, phone_number]):
        return json_response(
            {"error": "Missing required fields: firstname, lastname, birthday, phone_number"},
            status=400
        )

    try:
        birthday = datetime.strptime(birthday_str, "%Y-%m-%d").date()
    except ValueError:
        return json_response({"error": "birthday must be in YYYY-MM-DD format"}, status=400)

    a = Assistant(
        firstname=firstname,
        lastname=lastname,
        surname=data.get("surname"),
        birthday=birthday,
        phone_number=phone_number,
        email=data.get("email"),
    )
    db.session.add(a)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return json_response({"error": "IntegrityError", "details": str(e.orig)}, status=400)

    return json_response(assistant_to_dict(a), status=201)


@assistants_bp.route("/<int:assistant_id>", methods=["GET", "PUT", "DELETE"], strict_slashes=False)
def assistant_detail(assistant_id: int):
    a = Assistant.query.get(assistant_id)
    if not a:
        return json_response({"error": "Assistant not found"}, status=404)

    if request.method == "GET":
        return json_response(assistant_to_dict(a, with_groups=True))

    if request.method == "PUT":
        data = request.json or {}
        if "firstname" in data: a.firstname = data["firstname"]
        if "lastname" in data: a.lastname = data["lastname"]
        if "surname" in data: a.surname = data["surname"]
        if "phone_number" in data: a.phone_number = data["phone_number"]
        if "email" in data: a.email = data["email"]

        if "birthday" in data:
            try:
                a.birthday = datetime.strptime(data["birthday"], "%Y-%m-%d").date()
            except ValueError:
                return json_response({"error": "birthday must be in YYYY-MM-DD format"}, status=400)

        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            return json_response({"error": "IntegrityError", "details": str(e.orig)}, status=400)

        return json_response(assistant_to_dict(a, with_groups=True))

    # DELETE
    db.session.delete(a)
    db.session.commit()
    return json_response({"message": "Deleted successfully"})


@assistants_bp.route("/<int:assistant_id>/groups", methods=["GET"], strict_slashes=False)
def assistant_groups(assistant_id: int):
    a = Assistant.query.get(assistant_id)
    if not a:
        return json_response({"error": "Assistant not found"}, status=404)

    groups = [
        {
            "id": g.id,
            "name": g.name,
            "academic_year": g.academic_year,
            "course_id": g.course_id
        } for g in (a.groups or [])
    ]
    return json_response(groups)