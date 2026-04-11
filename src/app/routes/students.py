from flask import Blueprint, request, jsonify
from datetime import datetime

from src.app import db
from src.app.keycloak_auth import roles_required
from src.app.models import Student


students_bp = Blueprint('students', __name__)


@students_bp.route('/', methods=['GET'])
@roles_required('manager', 'admin')
def get_students():
    students = Student.query.all()
    return jsonify([{
        'id': s.id,
        'firstname': s.firstname,
        'lastname': s.lastname,
        'birthday': s.birthday.isoformat(),
        'group_name': s.group_name,
        'education_type': s.education_type
    } for s in students])


@students_bp.route('/<int:student_id>', methods=['GET'])
@roles_required('manager', 'admin')
def get_student(student_id):
    s = Student.query.get(student_id)
    if not s:
        return jsonify({'error': 'Student not found'}), 404

    return jsonify({
        'id': s.id,
        'firstname': s.firstname,
        'lastname': s.lastname,
        'birthday': s.birthday.isoformat(),
        'group_name': s.group_name,
        'education_type': s.education_type
    })


@students_bp.route('/', methods=['POST'])
@roles_required('manager', 'admin')
def create_student():
    data = request.json or {}

    required_fields = [
        'firstname',
        'lastname',
        'birthday',
        'address',
        'educational_institution',
        'group_name',
        'education_type',
    ]
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return jsonify({'error': f"Missing required fields: {', '.join(missing)}"}), 400

    try:
        birthday = datetime.strptime(data['birthday'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'birthday must be in YYYY-MM-DD format'}), 400

    s = Student(
        firstname=data['firstname'],
        lastname=data['lastname'],
        surname=data.get('surname'),
        phone_number=data.get('phone_number'),
        email=data.get('email'),
        birthday=birthday,
        address=data['address'],
        educational_institution=data['educational_institution'],
        group_name=data['group_name'],
        education_type=data['education_type'],
        enrolled_this_year=data.get('enrolled_this_year', False)
    )
    db.session.add(s)
    db.session.commit()
    return jsonify({'id': s.id}), 201


@students_bp.route('/<int:student_id>', methods=['PUT'])
@roles_required('manager', 'admin')
def update_student(student_id):
    s = Student.query.get(student_id)
    if not s:
        return jsonify({'error': 'Student not found'}), 404

    data = request.json or {}

    for key in [
        'firstname', 'lastname', 'surname', 'phone_number', 'email',
        'birthday', 'address', 'educational_institution', 'group_name',
        'education_type', 'enrolled_this_year'
    ]:
        if key in data:
            if key == 'birthday':
                try:
                    setattr(s, key, datetime.strptime(data[key], '%Y-%m-%d').date())
                except ValueError:
                    return jsonify({'error': 'birthday must be in YYYY-MM-DD format'}), 400
            else:
                setattr(s, key, data[key])

    db.session.commit()
    return jsonify({'message': 'Updated successfully'})


@students_bp.route('/<int:student_id>', methods=['DELETE'])
@roles_required('admin')
def delete_student(student_id):
    s = Student.query.get(student_id)
    if not s:
        return jsonify({'error': 'Student not found'}), 404

    db.session.delete(s)
    db.session.commit()
    return jsonify({'message': 'Deleted successfully'})