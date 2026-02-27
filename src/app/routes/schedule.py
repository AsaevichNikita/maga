from flask import Blueprint, request, Response
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import json

from src.app import db
from src.app.models import ScheduleSlot, CourseGroup, Classroom


schedule_bp = Blueprint("schedule", __name__, url_prefix="/schedule")


def json_response(data, status=200):
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype="application/json; charset=utf-8",
        status=status
    )


@schedule_bp.route("/", methods=["GET", "POST"], strict_slashes=False)
def slots_list_create():
    if request.method == "GET":
        group_id = request.args.get("group_id", type=int)
        q = ScheduleSlot.query
        if group_id:
            q = q.filter(ScheduleSlot.group_id == group_id)
        items = q.order_by(ScheduleSlot.id.asc()).all()
        return json_response([s.to_dict() for s in items])

    data = request.json or {}

    group_id = data.get("group_id")
    day_of_week = data.get("day_of_week")
    start_time_str = data.get("start_time")
    end_time_str = data.get("end_time")

    if not all([group_id, day_of_week, start_time_str, end_time_str]):
        return json_response(
            {"error": "Missing required fields: group_id, day_of_week, start_time, end_time"},
            status=400
        )

    group = CourseGroup.query.get(group_id)
    if not group:
        return json_response({"error": "group_id not found"}, status=400)

    try:
        start_time = datetime.strptime(start_time_str, "%H:%M").time()
        end_time = datetime.strptime(end_time_str, "%H:%M").time()
    except ValueError:
        return json_response({"error": "start_time/end_time must be HH:MM"}, status=400)

    classroom_id = data.get("classroom_id")
    classroom_name = data.get("classroom_name")

    classroom = None
    if classroom_id is not None:
        classroom = Classroom.query.get(classroom_id)
        if not classroom:
            return json_response({"error": "classroom_id not found"}, status=400)
    elif classroom_name:
        classroom = Classroom.query.filter_by(name=classroom_name).first()
        if not classroom:
            classroom = Classroom(name=classroom_name, capacity=15)
            db.session.add(classroom)
            db.session.flush()  # получим id до commit

    slot = ScheduleSlot(
        group_id=group_id,
        day_of_week=int(day_of_week),
        start_time=start_time,
        end_time=end_time,
        classroom_id=classroom.id if classroom else None
    )

    db.session.add(slot)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        # тут часто прилетит uq_schedule_slot_group (если пытаемся создать второй слот группе)
        return json_response({"error": "IntegrityError", "details": str(e.orig)}, status=400)

    return json_response(slot.to_dict(), status=201)


@schedule_bp.route("/<int:slot_id>", methods=["GET", "PUT", "DELETE"], strict_slashes=False)
def slot_detail(slot_id: int):
    s = ScheduleSlot.query.get(slot_id)
    if not s:
        return json_response({"error": "ScheduleSlot not found"}, status=404)

    if request.method == "GET":
        return json_response(s.to_dict())

    if request.method == "PUT":
        data = request.json or {}
        if "day_of_week" in data: s.day_of_week = int(data["day_of_week"])

        if "start_time" in data:
            try:
                s.start_time = datetime.strptime(data["start_time"], "%H:%M").time()
            except ValueError:
                return json_response({"error": "start_time must be HH:MM"}, status=400)

        if "end_time" in data:
            try:
                s.end_time = datetime.strptime(data["end_time"], "%H:%M").time()
            except ValueError:
                return json_response({"error": "end_time must be HH:MM"}, status=400)

        if "classroom_id" in data:
            cid = data["classroom_id"]
            if cid is None:
                s.classroom_id = None
            else:
                c = Classroom.query.get(cid)
                if not c:
                    return json_response({"error": "classroom_id not found"}, status=400)
                s.classroom_id = c.id

        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            return json_response({"error": "IntegrityError", "details": str(e.orig)}, status=400)

        return json_response(s.to_dict())

    db.session.delete(s)
    db.session.commit()
    return json_response({"message": "Deleted successfully"})








