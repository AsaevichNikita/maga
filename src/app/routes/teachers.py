from flask import Blueprint, request, Response
from src.app import db
from src.app.models import Teacher
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import json

teachers_bp = Blueprint('teachers', __name__, url_prefix='/teachers')

def json_response(data, status=200):
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype='application/json; charset=utf-8',
        status=status
    )

def teacher_to_dict(t: Teacher):
    return {
        "id": t.id,
        "firstname": t.firstname,
        "lastname": t.lastname,
        "surname": t.surname,
        "birthday": t.birthday.isoformat() if t.birthday else None,
        "phone_number": t.phone_number,
        "email": t.email
    }

# ------------------------
# GET /teachers/  (список)
# POST /teachers/ (создание)
# ------------------------
@teachers_bp.route('/', methods=['GET', 'POST'], strict_slashes=False)
def teachers_list_create():
    if request.method == 'GET':
        teachers = Teacher.query.all()
        return json_response([teacher_to_dict(t) for t in teachers])

    data = request.json or {}

    # обязательные поля
    firstname = data.get('firstname')
    lastname = data.get('lastname')
    email = data.get('email')
    birthday_str = data.get('birthday')

    if not all([firstname, lastname, email, birthday_str]):
        return json_response({"error": "Missing required fields: firstname, lastname, email, birthday"}, status=400)

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
        email=email
    )

    db.session.add(teacher)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return json_response({"error": "Teacher with this email already exists"}, status=400)

    return json_response(teacher_to_dict(teacher), status=201)

# ------------------------
# GET /teachers/<id>
# PUT /teachers/<id>
# DELETE /teachers/<id>
# ------------------------
@teachers_bp.route('/<int:teacher_id>', methods=['GET', 'PUT', 'DELETE'], strict_slashes=False)
def teacher_detail(teacher_id):
    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        return json_response({"error": "Teacher not found"}, status=404)

    if request.method == 'GET':
        return json_response(teacher_to_dict(teacher))

    if request.method == 'PUT':
        data = request.json or {}

        if 'firstname' in data: teacher.firstname = data['firstname']
        if 'lastname' in data: teacher.lastname = data['lastname']
        if 'surname' in data: teacher.surname = data['surname']
        if 'phone_number' in data: teacher.phone_number = data['phone_number']
        if 'email' in data: teacher.email = data['email']

        if 'birthday' in data:
            try:
                teacher.birthday = datetime.strptime(data['birthday'], "%Y-%m-%d").date()
            except ValueError:
                return json_response({"error": "birthday must be in YYYY-MM-DD format"}, status=400)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return json_response({"error": "Email must be unique"}, status=400)

        return json_response(teacher_to_dict(teacher))

    # DELETE
    db.session.delete(teacher)
    db.session.commit()
    return json_response({"message": "Deleted successfully"})