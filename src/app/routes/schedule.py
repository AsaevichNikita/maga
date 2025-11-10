from flask import Blueprint, request, Response
from src.app import db
from app.models import ScheduleSlot, Course, ReservedTime
import json
from datetime import datetime, time

schedule_bp = Blueprint('schedule', __name__)

def json_response(data, status=200):
    """Возвращает JSON с поддержкой русских символов"""
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype='application/json; charset=utf-8',
        status=status
    )

# ------------------------
# CRUD слотов
# ------------------------
@schedule_bp.route('/', methods=['GET', 'POST'])
def slots_list_create():
    """
    Получение списка слотов или создание нового
    ---
    get:
      description: Получить список всех слотов
      responses:
        200:
          description: Список слотов
    post:
      description: Создать новый слот
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - course_id
                - day_of_week
                - start_time
                - end_time
                - classroom
              properties:
                course_id:
                  type: integer
                day_of_week:
                  type: integer
                start_time:
                  type: string
                  example: "09:00"
                end_time:
                  type: string
                  example: "10:30"
                classroom:
                  type: string
      responses:
        201:
          description: Слот успешно создан
        400:
          description: Ошибка данных или конфликт времени
    """
    if request.method == 'GET':
        slots = ScheduleSlot.query.all()
        return json_response([s.to_dict() for s in slots])

    if request.method == 'POST':
        data = request.json
        course_id = data.get('course_id')
        day_of_week = data.get('day_of_week')
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')
        classroom = data.get('classroom')

        if not all([course_id, day_of_week, start_time_str, end_time_str, classroom]):
            return json_response({'error': 'Missing fields'}, status=400)

        course = Course.query.get(course_id)
        if not course:
            return json_response({'error': 'Course not found'}, status=404)

        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()

        # Проверка пересечения преподавателя
        conflict = ScheduleSlot.query.join(Course).filter(
            Course.teacher_id == course.teacher_id,
            ScheduleSlot.day_of_week == day_of_week,
            db.or_(
                db.and_(ScheduleSlot.start_time <= start_time, ScheduleSlot.end_time > start_time),
                db.and_(ScheduleSlot.start_time < end_time, ScheduleSlot.end_time >= end_time),
                db.and_(ScheduleSlot.start_time >= start_time, ScheduleSlot.end_time <= end_time)
            )
        ).first()
        if conflict:
            return json_response({'error': 'Преподаватель уже ведет занятие в это время'}, status=400)

        # Проверка пересечения аудитории
        conflict_room = ScheduleSlot.query.filter_by(
            day_of_week=day_of_week,
            classroom=classroom
        ).filter(
            db.or_(
                db.and_(ScheduleSlot.start_time <= start_time, ScheduleSlot.end_time > start_time),
                db.and_(ScheduleSlot.start_time < end_time, ScheduleSlot.end_time >= end_time),
                db.and_(ScheduleSlot.start_time >= start_time, ScheduleSlot.end_time <= end_time)
            )
        ).first()
        if conflict_room:
            return json_response({'error': 'Аудитория занята в это время'}, status=400)

        slot = ScheduleSlot(
            course_id=course_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            classroom=classroom
        )
        db.session.add(slot)
        db.session.commit()
        return json_response(slot.to_dict(), status=201)

# ------------------------
# CRUD конкретного слота
# ------------------------
@schedule_bp.route('/<int:slot_id>', methods=['GET','PUT','DELETE'])
def slot_detail(slot_id):
    """
    Получение, обновление или удаление слота по ID
    ---
    parameters:
      - name: slot_id
        in: path
        required: true
        schema:
          type: integer
    get:
      description: Получить слот
      responses:
        200:
          description: Данные слота
        404:
          description: Слот не найден
    put:
      description: Обновить слот
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                start_time:
                  type: string
                  example: "10:45"
                end_time:
                  type: string
                  example: "12:15"
                classroom:
                  type: string
      responses:
        200:
          description: Слот успешно обновлен
        400:
          description: Конфликт времени
        404:
          description: Слот не найден
    delete:
      description: Удалить слот
      responses:
        200:
          description: Слот успешно удален
        404:
          description: Слот не найден
    """
    slot = ScheduleSlot.query.get(slot_id)
    if not slot:
        return json_response({'error': 'Slot not found'}, status=404)

    if request.method == 'GET':
        return json_response(slot.to_dict())

    if request.method == 'PUT':
        data = request.json
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')
        classroom = data.get('classroom')

        start_time = datetime.strptime(start_time_str, '%H:%M').time() if start_time_str else slot.start_time
        end_time = datetime.strptime(end_time_str, '%H:%M').time() if end_time_str else slot.end_time
        classroom = classroom if classroom else slot.classroom

        conflict = ScheduleSlot.query.join(Course).filter(
            Course.teacher_id == slot.course.teacher_id,
            ScheduleSlot.day_of_week == slot.day_of_week,
            ScheduleSlot.id != slot.id,
            db.or_(
                db.and_(ScheduleSlot.start_time <= start_time, ScheduleSlot.end_time > start_time),
                db.and_(ScheduleSlot.start_time < end_time, ScheduleSlot.end_time >= end_time),
                db.and_(ScheduleSlot.start_time >= start_time, ScheduleSlot.end_time <= end_time)
            )
        ).first()
        if conflict:
            return json_response({'error': 'Преподаватель уже ведет занятие в это время'}, status=400)

        conflict_room = ScheduleSlot.query.filter(
            ScheduleSlot.day_of_week == slot.day_of_week,
            ScheduleSlot.classroom == classroom,
            ScheduleSlot.id != slot.id
        ).filter(
            db.or_(
                db.and_(ScheduleSlot.start_time <= start_time, ScheduleSlot.end_time > start_time),
                db.and_(ScheduleSlot.start_time < end_time, ScheduleSlot.end_time >= end_time),
                db.and_(ScheduleSlot.start_time >= start_time, ScheduleSlot.end_time <= end_time)
            )
        ).first()
        if conflict_room:
            return json_response({'error': 'Аудитория занята в это время'}, status=400)

        slot.start_time = start_time
        slot.end_time = end_time
        slot.classroom = classroom
        db.session.commit()
        return json_response(slot.to_dict())

    if request.method == 'DELETE':
        db.session.delete(slot)
        db.session.commit()
        return json_response({'message': 'Deleted successfully'})








