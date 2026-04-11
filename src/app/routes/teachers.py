from datetime import datetime
import json

from flask import Blueprint, Response, request
from sqlalchemy.exc import IntegrityError

from src.app import db
from src.app.current_user import get_current_teacher
from src.app.keycloak_auth import roles_required
from src.app.models import Teacher


teachers_bp = Blueprint('teachers', __name__)


def json_response(data, status=200):
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype='application/json; charset=utf-8',
        status=status,
    )


def teacher_to_dict(t: Teacher):
    return {
        "id": t.id,
        "firstname": t.firstname,
        "lastname": t.lastname,
        "surname": t.surname,
        "birthday": t.birthday.isoformat() if t.birthday else None,
        "phone_number": t.phone_number,
        "email": t.email,
        "keycloak_user_id": t.keycloak_user_id,
    }


def teacher_schedule_to_dict(t: Teacher):
    rows = []
    groups = sorted(
        t.lead_groups or [],
        key=lambda g: (
            g.schedule_slot.day_of_week if g.schedule_slot else 99,
            g.schedule_slot.start_time.strftime('%H:%M') if g.schedule_slot and g.schedule_slot.start_time else '99:99',
            g.id,
        ),
    )

    for group in groups:
        slot = group.schedule_slot
        rows.append({
            "group_id": group.id,
            "group_name": group.name,
            "academic_year": group.academic_year,
            "course_id": group.course_id,
            "course_name": group.course.name if group.course else None,
            "block_id": group.block_id,
            "block_name": group.informatics_block.name if group.informatics_block else None,
            "day_of_week": slot.day_of_week if slot else None,
            "start_time": slot.start_time.strftime('%H:%M') if slot and slot.start_time else None,
            "end_time": slot.end_time.strftime('%H:%M') if slot and slot.end_time else None,
            "classroom_id": slot.classroom_id if slot else None,
            "classroom_name": slot.classroom.name if slot and slot.classroom else None,
            "classroom_capacity": slot.classroom.capacity if slot and slot.classroom else None,
        })

    return {
        "teacher": teacher_to_dict(t),
        "schedule": rows,
        "schedule_count": len(rows),
    }


@teachers_bp.route('/me', methods=['GET'], strict_slashes=False)
@roles_required('teacher', 'admin')
def get_my_teacher_profile():
    teacher = get_current_teacher()
    if not teacher:
        return json_response({"error": "Teacher profile is not linked to current Keycloak user"}, status=404)
    return json_response(teacher_to_dict(teacher))


@teachers_bp.route('/me/schedule', methods=['GET'], strict_slashes=False)
@roles_required('teacher', 'admin')
def get_my_teacher_schedule():
    teacher = get_current_teacher()
    if not teacher:
        return json_response({"error": "Teacher profile is not linked to current Keycloak user"}, status=404)
    return json_response(teacher_schedule_to_dict(teacher))


@teachers_bp.route('/', methods=['GET'], strict_slashes=False)
@roles_required('manager', 'admin')
def get_teachers():
    teachers = Teacher.query.all()
    return json_response([teacher_to_dict(t) for t in teachers])


@teachers_bp.route('/', methods=['POST'], strict_slashes=False)
@roles_required('manager', 'admin')
def create_teacher():
    data = request.json or {}

    firstname = data.get('firstname')
    lastname = data.get('lastname')
    email = data.get('email')
    birthday_str = data.get('birthday')

    if not all([firstname, lastname, email, birthday_str]):
        return json_response(
            {"error": "Missing required fields: firstname, lastname, email, birthday"},
            status=400,
        )

    try:
        birthday = datetime.strptime(birthday_str, "%Y-%m-%d").date()
    except ValueError:
        return json_response({"error": "birthday must be in YYYY-MM-DD format"}, status=400)

    teacher = Teacher(
        firstname=firstname,
        lastname=lastname,
        surname=data.get('surname'),
        birthday=birthday,
        phone_number=data.get('phone_number'),
        email=email,
        keycloak_user_id=data.get('keycloak_user_id'),
    )

    db.session.add(teacher)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return json_response({"error": "Teacher with this email or keycloak_user_id already exists"}, status=400)

    return json_response(teacher_to_dict(teacher), status=201)


@teachers_bp.route('/<int:teacher_id>', methods=['GET'], strict_slashes=False)
@roles_required('manager', 'admin')
def get_teacher(teacher_id):
    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        return json_response({"error": "Teacher not found"}, status=404)

    return json_response(teacher_to_dict(teacher))


@teachers_bp.route('/<int:teacher_id>', methods=['PUT'], strict_slashes=False)
@roles_required('manager', 'admin')
def update_teacher(teacher_id):
    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        return json_response({"error": "Teacher not found"}, status=404)

    data = request.json or {}

    if 'firstname' in data:
        teacher.firstname = data['firstname']
    if 'lastname' in data:
        teacher.lastname = data['lastname']
    if 'surname' in data:
        teacher.surname = data['surname']
    if 'phone_number' in data:
        teacher.phone_number = data['phone_number']
    if 'email' in data:
        teacher.email = data['email']
    if 'keycloak_user_id' in data:
        teacher.keycloak_user_id = data['keycloak_user_id']

    if 'birthday' in data:
        try:
            teacher.birthday = datetime.strptime(data['birthday'], "%Y-%m-%d").date()
        except ValueError:
            return json_response({"error": "birthday must be in YYYY-MM-DD format"}, status=400)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return json_response({"error": "Email or keycloak_user_id must be unique"}, status=400)

    return json_response(teacher_to_dict(teacher))


@teachers_bp.route('/<int:teacher_id>', methods=['DELETE'], strict_slashes=False)
@roles_required('admin')
def delete_teacher(teacher_id):
    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        return json_response({"error": "Teacher not found"}, status=404)

    db.session.delete(teacher)
    db.session.commit()
    return json_response({"message": "Deleted successfully"})
