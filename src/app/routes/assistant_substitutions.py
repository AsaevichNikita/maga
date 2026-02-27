from flask import Blueprint, request, Response
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import json

from src.app import db
from src.app.models import AssistantSubstitution, CourseGroup, Assistant


assistant_substitutions_bp = Blueprint(
    "assistant_substitutions", __name__, url_prefix="/assistant-substitutions"
)


def json_response(data, status=200):
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype="application/json; charset=utf-8",
        status=status
    )


def sub_to_dict(s: AssistantSubstitution):
    return {
        "id": s.id,
        "group_id": s.group_id,
        "date": s.date.isoformat() if s.date else None,
        "substitute_assistant_id": s.substitute_assistant_id,
        "replaced_assistant_id": s.replaced_assistant_id,
        "note": s.note,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


@assistant_substitutions_bp.route("/", methods=["GET", "POST"], strict_slashes=False)
def subs_list_create():
    if request.method == "GET":
        group_id = request.args.get("group_id", type=int)
        date_str = request.args.get("date")

        q = AssistantSubstitution.query
        if group_id:
            q = q.filter(AssistantSubstitution.group_id == group_id)
        if date_str:
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d").date()
                q = q.filter(AssistantSubstitution.date == d)
            except ValueError:
                return json_response({"error": "date must be YYYY-MM-DD"}, status=400)

        items = q.order_by(AssistantSubstitution.id.asc()).all()
        return json_response([sub_to_dict(x) for x in items])

    data = request.json or {}
    group_id = data.get("group_id")
    date_str = data.get("date")
    substitute_assistant_id = data.get("substitute_assistant_id")
    replaced_assistant_id = data.get("replaced_assistant_id")

    if not all([group_id, date_str, substitute_assistant_id]):
        return json_response(
            {"error": "Missing required fields: group_id, date, substitute_assistant_id"},
            status=400
        )

    if not CourseGroup.query.get(group_id):
        return json_response({"error": "group_id not found"}, status=400)
    if not Assistant.query.get(substitute_assistant_id):
        return json_response({"error": "substitute_assistant_id not found"}, status=400)
    if replaced_assistant_id is not None and not Assistant.query.get(replaced_assistant_id):
        return json_response({"error": "replaced_assistant_id not found"}, status=400)

    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return json_response({"error": "date must be YYYY-MM-DD"}, status=400)

    s = AssistantSubstitution(
        group_id=group_id,
        date=d,
        substitute_assistant_id=substitute_assistant_id,
        replaced_assistant_id=replaced_assistant_id,
        note=data.get("note"),
    )
    db.session.add(s)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return json_response({"error": "IntegrityError", "details": str(e.orig)}, status=400)

    return json_response(sub_to_dict(s), status=201)


@assistant_substitutions_bp.route("/<int:sub_id>", methods=["GET", "PUT", "DELETE"], strict_slashes=False)
def sub_detail(sub_id: int):
    s = AssistantSubstitution.query.get(sub_id)
    if not s:
        return json_response({"error": "AssistantSubstitution not found"}, status=404)

    if request.method == "GET":
        return json_response(sub_to_dict(s))

    if request.method == "PUT":
        data = request.json or {}

        if "note" in data:
            s.note = data["note"]

        if "replaced_assistant_id" in data:
            rid = data["replaced_assistant_id"]
            if rid is not None and not Assistant.query.get(rid):
                return json_response({"error": "replaced_assistant_id not found"}, status=400)
            s.replaced_assistant_id = rid

        db.session.commit()
        return json_response(sub_to_dict(s))

    db.session.delete(s)
    db.session.commit()
    return json_response({"message": "Deleted successfully"})