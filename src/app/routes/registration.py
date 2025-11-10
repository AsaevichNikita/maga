from flask import Blueprint, request, Response
from src.app import db
from app.models import Student, ScheduleSlot, CourseRegistration, Course
from sqlalchemy.exc import IntegrityError
from datetime import datetime, time
import json

registration_bp = Blueprint('registration', __name__, url_prefix='/registration')

def json_response(data, status=200):
    """Возвращает JSON с поддержкой русских символов"""
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype='application/json; charset=utf-8',
        status=status
    )

# ------------------------
# Разрешённые временные диапазоны
# ------------------------
ALLOWED_TIME_RANGES = [
    (time(9, 0), time(10, 30)),
    (time(10, 45), time(12, 15)),
    (time(13, 0), time(14, 30)),
    (time(14, 45), time(16, 15)),
]

def is_time_allowed(start_time, end_time):
    """Проверяет, входит ли время занятия в разрешённые интервалы"""
    for allowed_start, allowed_end in ALLOWED_TIME_RANGES:
        if start_time >= allowed_start and end_time <= allowed_end:
            return True
    return False

# ------------------------
# Запись студента на курс
# ------------------------
@registration_bp.route('/enroll', methods=['POST'])
def enroll_student():
    """
    Записать студента на курс
    ---
    post:
      description: Записать студента на курс по ID
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - student_id
                - slot_id
              properties:
                student_id:
                  type: integer
                slot_id:
                  type: integer
      responses:
        200:
          description: Студент успешно записан
        400:
          description: Ошибка данных, время не разрешено или курс полный
        404:
          description: Студент или слот не найден
    """
    data = request.json
    student_id = data.get('student_id')
    slot_id = data.get('slot_id')

    if not all([student_id, slot_id]):
        return json_response({'error': 'student_id и slot_id обязательны'}, status=400)

    student = Student.query.get(student_id)
    slot = ScheduleSlot.query.get(slot_id)

    if not student or not slot:
        return json_response({'error': 'Student or slot not found'}, status=404)

    course = slot.course
    if not course or not course.is_active:
        return json_response({'error': 'Курс не найден или не активен'}, status=400)

    previous_registration = CourseRegistration.query.filter_by(
        student_id=student.id,
        course_id=course.id
    ).first()

    if previous_registration:
        return json_response({'error': 'Студент уже проходил этот курс ранее'}, status=400)

    if not is_time_allowed(slot.start_time, slot.end_time):
        return json_response({'error': 'Выбранное время не разрешено для занятий'}, status=400)

    active_students = CourseRegistration.query.filter_by(
        course_id=course.id, status='approved'
    ).count()
    if active_students >= course.max_students:
        return json_response({'error': 'Нет свободных мест на курсе'}, status=400)

    registration = CourseRegistration(
        student_id=student.id,
        course_id=course.id,
        schedule_slot_id=slot.id,
        status='approved'
    )

    db.session.add(registration)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return json_response({'error': 'Ошибка при записи студента'}, status=400)

    return json_response({
        'message': 'Студент успешно записан на курс',
        'registration': {
            'id': registration.id,
            'student_id': student.id,
            'course_id': course.id,
            'slot_id': slot.id,
            'status': registration.status
        }
    })

# ------------------------
# Фильтрация доступных слотов
# ------------------------
@registration_bp.route('/filter_slots', methods=['GET'])
def filter_slots():
    """
    Получение слотов по фильтрам
    ---
    get:
      description: Фильтрация слотов по course_id, classroom и дню недели
      parameters:
        - name: course_id
          in: query
          schema:
            type: integer
        - name: classroom
          in: query
          schema:
            type: string
        - name: day
          in: query
          schema:
            type: integer
      responses:
        200:
          description: Список слотов по фильтрам
    """
    course_id = request.args.get('course_id', type=int)
    classroom = request.args.get('classroom')
    day = request.args.get('day', type=int)

    query = ScheduleSlot.query
    if course_id:
        query = query.filter_by(course_id=course_id)
    if classroom:
        query = query.filter_by(classroom=classroom)
    if day:
        query = query.filter_by(day_of_week=day)

    slots = [s.to_dict() for s in query.all()]
    return json_response(slots)

# ------------------------
# Завершение обучения
# ------------------------
@registration_bp.route('/complete/<int:registration_id>', methods=['POST'])
def complete_course(registration_id):
    """
    Завершение курса для регистрации
    ---
    post:
      description: Отметить курс как завершённый
      parameters:
        - name: registration_id
          in: path
          required: true
          schema:
            type: integer
      responses:
        200:
          description: Курс отмечен как завершённый
        404:
          description: Регистрация не найдена
    """
    reg = CourseRegistration.query.get(registration_id)
    if not reg:
        return json_response({'error': 'Registration not found'}, status=404)

    reg.status = 'completed'
    db.session.commit()
    return json_response({'message': 'Course marked as completed'})

