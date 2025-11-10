from flask import Blueprint, request, Response
from src.app import db
from app.models import Course, CourseCategory, Teacher, ScheduleSlot, Student, CourseRegistration
import json
from datetime import datetime

courses_bp = Blueprint('courses', __name__, url_prefix='/courses')

def json_response(data, status=200):
    """Возвращает JSON с поддержкой русских символов"""
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype='application/json; charset=utf-8',
        status=status
    )

# ------------------------
# CRUD курсов
# ------------------------
@courses_bp.route('/', methods=['GET', 'POST'], strict_slashes=False)
def courses_list_create():
    """
    Получение списка курсов или создание нового
    ---
    get:
      description: Получить список курсов с фильтрацией по category_id, teacher_id, is_active
      parameters:
        - name: category_id
          in: query
          schema:
            type: integer
        - name: teacher_id
          in: query
          schema:
            type: integer
        - name: is_active
          in: query
          schema:
            type: integer
      responses:
        200:
          description: Список курсов
    post:
      description: Создать новый курс
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - name
                - category_id
                - teacher_id
              properties:
                name:
                  type: string
                category_id:
                  type: integer
                teacher_id:
                  type: integer
                max_students:
                  type: integer
                duration_minutes:
                  type: integer
                price:
                  type: number
                is_active:
                  type: boolean
                description:
                  type: string
      responses:
        201:
          description: Курс создан
        400:
          description: Отсутствуют обязательные поля
    """
    if request.method == 'GET':
        category_id = request.args.get('category_id', type=int)
        teacher_id = request.args.get('teacher_id', type=int)
        is_active = request.args.get('is_active', type=int)  # 1 или 0

        query = Course.query
        if category_id:
            query = query.filter(Course.category_id == category_id)
        if teacher_id:
            query = query.filter(Course.teacher_id == teacher_id)
        if is_active is not None:
            query = query.filter(Course.is_active == bool(is_active))

        courses = [c.to_dict() for c in query.all()]
        return json_response(courses)

    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        category_id = data.get('category_id')
        teacher_id = data.get('teacher_id')
        max_students = data.get('max_students', 15)
        duration_minutes = data.get('duration_minutes', 90)
        price = data.get('price', 0)
        is_active = data.get('is_active', True)
        description = data.get('description')

        if not all([name, category_id, teacher_id]):
            return json_response({'error': 'Missing required fields'}, status=400)

        course = Course(
            name=name,
            category_id=category_id,
            teacher_id=teacher_id,
            max_students=max_students,
            duration_minutes=duration_minutes,
            price=price,
            is_active=is_active,
            description=description
        )
        db.session.add(course)
        db.session.commit()
        return json_response(course.to_dict(), status=201)

# ------------------------
# CRUD конкретного курса
# ------------------------
@courses_bp.route('/<int:course_id>', methods=['GET', 'PUT', 'DELETE'], strict_slashes=False)
def course_detail(course_id):
    """
    Получение, обновление или удаление курса по ID
    ---
    parameters:
      - name: course_id
        in: path
        required: true
        schema:
          type: integer
    get:
      description: Получить данные курса
      responses:
        200:
          description: Данные курса
        404:
          description: Курс не найден
    put:
      description: Обновить курс
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        200:
          description: Курс обновлён
        404:
          description: Курс не найден
    delete:
      description: Удалить курс
      responses:
        200:
          description: Курс удалён
        404:
          description: Курс не найден
    """

    course = Course.query.get(course_id)
    if not course:
        return json_response({'error': 'Course not found'}, status=404)

    if request.method == 'GET':
        return json_response(course.to_dict())
    if request.method == 'PUT':
        data = request.json
        course.name = data.get('name', course.name)
        course.category_id = data.get('category_id', course.category_id)
        course.teacher_id = data.get('teacher_id', course.teacher_id)
        course.max_students = data.get('max_students', course.max_students)
        course.duration_minutes = data.get('duration_minutes', course.duration_minutes)
        course.price = data.get('price', course.price)
        course.is_active = data.get('is_active', course.is_active)
        course.description = data.get('description', course.description)
        db.session.commit()
        return json_response(course.to_dict())
    if request.method == 'DELETE':
        db.session.delete(course)
        db.session.commit()
        return json_response({'message': 'Deleted successfully'})

# ------------------------
# Слоты курса
# ------------------------
@courses_bp.route('/<int:course_id>/slots', methods=['GET'], strict_slashes=False)
def course_slots(course_id):
    """
    Получить слоты курса
    ---
    parameters:
      - name: course_id
        in: path
        required: true
        schema:
          type: integer
    get:
      description: Список слотов курса
      responses:
        200:
          description: Слоты курса
        404:
          description: Курс не найден
    """
    course = Course.query.get(course_id)
    if not course:
        return json_response({'error': 'Course not found'}, status=404)
    slots = [s.to_dict() for s in course.schedule_slots]
    return json_response(slots)

# ------------------------
# Студенты курса
# ------------------------
@courses_bp.route('/<int:course_id>/students', methods=['GET'], strict_slashes=False)
def course_students(course_id):
    """
    Получить список студентов курса
    ---
    parameters:
      - name: course_id
        in: path
        required: true
        schema:
          type: integer
    get:
      description: Список студентов курса
      responses:
        200:
          description: Студенты курса
        404:
          description: Курс не найден
    """
    course = Course.query.get(course_id)
    if not course:
        return json_response({'error': 'Course not found'}, status=404)
    students = [
        {
            'id': s.id,
            'firstname': s.firstname,
            'lastname': s.lastname,
            'birthday': s.birthday.isoformat(),
            'group_name': s.group_name,
            'education_type': s.education_type
        }
        for s in course.students
    ]
    return json_response(students)

# ------------------------
# Завершение регистрации
# ------------------------
@courses_bp.route('/complete_registration/<int:registration_id>', methods=['POST'], strict_slashes=False)
def complete_registration(registration_id):
    """
    Завершить регистрацию на курс
    ---
    parameters:
      - name: registration_id
        in: path
        required: true
        schema:
          type: integer
    post:
      description: Отметить регистрацию как завершённую
      responses:
        200:
          description: Регистрация завершена
        404:
          description: Регистрация не найдена
    """
    reg = CourseRegistration.query.get(registration_id)
    if not reg:
        return json_response({'error': 'Registration not found'}, status=404)
    reg.completed = True
    reg.completed_at = datetime.utcnow()
    db.session.commit()
    return json_response({'message': 'Registration marked as completed'})

