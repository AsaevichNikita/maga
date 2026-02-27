from flask import Blueprint, request, jsonify
from src.app.models import Student
from src.app import db
from datetime import datetime

students_bp = Blueprint('students', __name__, url_prefix='/students')

# ------------------------
# GET /students/ - список всех студентов
# ------------------------
@students_bp.route('/', methods=['GET'])
def get_students():
    """
    Получить список всех студентов
    ---
    responses:
      200:
        description: Список студентов
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  firstname:
                    type: string
                  lastname:
                    type: string
                  birthday:
                    type: string
                    format: date
                  group_name:
                    type: string
                  education_type:
                    type: string
    """
    students = Student.query.all()
    return jsonify([{
        'id': s.id,
        'firstname': s.firstname,
        'lastname': s.lastname,
        'birthday': s.birthday.isoformat(),
        'group_name': s.group_name,
        'education_type': s.education_type
    } for s in students])

# ------------------------
# GET /students/<id> - конкретный студент
# ------------------------
@students_bp.route('/<int:student_id>', methods=['GET'])
def get_student(student_id):
    """
    Получить конкретного студента по ID
    ---
    parameters:
      - name: student_id
        in: path
        type: integer
        required: true
        description: ID студента
    responses:
      200:
        description: Данные студента
        content:
          application/json:
            schema:
              type: object
              properties:
                id:
                  type: integer
                firstname:
                  type: string
                lastname:
                  type: string
                birthday:
                  type: string
                  format: date
                group_name:
                  type: string
                education_type:
                  type: string
      404:
        description: Студент не найден
    """
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

# ------------------------
# POST /students/ - создать студента
# ------------------------
@students_bp.route('/', methods=['POST'])
def create_student():
    """
    Создать нового студента
    ---
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - firstname
              - lastname
              - birthday
              - address
              - educational_institution
              - group_name
              - education_type
            properties:
              firstname:
                type: string
              lastname:
                type: string
              surname:
                type: string
              phone_number:
                type: string
              email:
                type: string
              birthday:
                type: string
                format: date
              address:
                type: string
              educational_institution:
                type: string
              group_name:
                type: string
              education_type:
                type: string
              enrolled_this_year:
                type: boolean
    responses:
      201:
        description: Студент успешно создан
        content:
          application/json:
            schema:
              type: object
              properties:
                id:
                  type: integer
      400:
        description: Ошибка данных
    """
    data = request.json
    s = Student(
        firstname=data['firstname'],
        lastname=data['lastname'],
        surname=data.get('surname'),
        phone_number=data.get('phone_number'),
        email=data.get('email'),
        birthday=datetime.strptime(data['birthday'], '%Y-%m-%d').date(),
        address=data['address'],
        educational_institution=data['educational_institution'],
        group_name=data['group_name'],
        education_type=data['education_type'],
        enrolled_this_year=data.get('enrolled_this_year', False)
    )
    db.session.add(s)
    db.session.commit()
    return jsonify({'id': s.id}), 201

# ------------------------
# PUT /students/<id> - обновить студента
# ------------------------
@students_bp.route('/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    """
    Обновить данные студента
    ---
    parameters:
      - name: student_id
        in: path
        type: integer
        required: true
        description: ID студента
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              firstname:
                type: string
              lastname:
                type: string
              surname:
                type: string
              phone_number:
                type: string
              email:
                type: string
              birthday:
                type: string
                format: date
              address:
                type: string
              educational_institution:
                type: string
              group_name:
                type: string
              education_type:
                type: string
              enrolled_this_year:
                type: boolean
    responses:
      200:
        description: Студент успешно обновлён
      404:
        description: Студент не найден
    """
    s = Student.query.get(student_id)
    if not s:
        return jsonify({'error': 'Student not found'}), 404
    data = request.json
    for key in ['firstname','lastname','surname','phone_number','email','birthday','address','educational_institution','group_name','education_type','enrolled_this_year']:
        if key in data:
            if key == 'birthday':
                setattr(s, key, datetime.strptime(data[key], '%Y-%m-%d').date())
            else:
                setattr(s, key, data[key])
    db.session.commit()
    return jsonify({'message': 'Updated successfully'})

# ------------------------
# DELETE /students/<id> - удалить студента
# ------------------------
@students_bp.route('/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """
    Удалить студента
    ---
    parameters:
      - name: student_id
        in: path
        type: integer
        required: true
        description: ID студента
    responses:
      200:
        description: Студент успешно удалён
      404:
        description: Студент не найден
    """
    s = Student.query.get(student_id)
    if not s:
        return jsonify({'error': 'Student not found'}), 404
    db.session.delete(s)
    db.session.commit()
    return jsonify({'message': 'Deleted successfully'})

