from datetime import time
from src.app import db
from app.models import ScheduleSlot, CourseRegistration, Student, Teacher

def validate_schedule_conflicts(teacher_id, day_of_week, start_time, end_time, exclude_slot_id=None):
    """
    Проверяет конфликты расписания для преподавателя.
    Возвращает True если конфликтов нет, False если есть конфликт.
    """
    # Ищем слоты которые пересекаются по времени
    conflicting_slots = db.session.query(ScheduleSlot).\
        join(Course, ScheduleSlot.course_id == Course.id).\
        filter(Course.teacher_id == teacher_id).\
        filter(ScheduleSlot.day_of_week == day_of_week).\
        filter(
            ((ScheduleSlot.start_time <= start_time) & (ScheduleSlot.end_time > start_time)) |
            ((ScheduleSlot.start_time < end_time) & (ScheduleSlot.end_time >= end_time)) |
            ((ScheduleSlot.start_time >= start_time) & (ScheduleSlot.end_time <= end_time))
        )
    
    if exclude_slot_id:
        conflicting_slots = conflicting_slots.filter(ScheduleSlot.id != exclude_slot_id)
    
    return conflicting_slots.count() == 0

def validate_student_schedule_conflicts(student_id, day_of_week, start_time, end_time, exclude_slot_id=None):
    """
    Проверяет конфликты расписания для студента.
    """
    # Ищем курсы студента в это же время
    conflicting_slots = db.session.query(ScheduleSlot).\
        join(CourseRegistration, ScheduleSlot.course_id == CourseRegistration.course_id).\
        filter(CourseRegistration.student_id == student_id).\
        filter(CourseRegistration.status == 'approved').\
        filter(ScheduleSlot.day_of_week == day_of_week).\
        filter(
            ((ScheduleSlot.start_time <= start_time) & (ScheduleSlot.end_time > start_time)) |
            ((ScheduleSlot.start_time < end_time) & (ScheduleSlot.end_time >= end_time)) |
            ((ScheduleSlot.start_time >= start_time) & (ScheduleSlot.end_time <= end_time))
        )
    
    if exclude_slot_id:
        conflicting_slots = conflicting_slots.filter(ScheduleSlot.id != exclude_slot_id)
    
    return conflicting_slots.count() == 0

def validate_classroom_availability(building_id, classroom, day_of_week, start_time, end_time, exclude_slot_id=None):
    """
    Проверяет доступность аудитории.
    """
    conflicting_slots = db.session.query(ScheduleSlot).\
        filter(ScheduleSlot.building_id == building_id).\
        filter(ScheduleSlot.classroom == classroom).\
        filter(ScheduleSlot.day_of_week == day_of_week).\
        filter(
            ((ScheduleSlot.start_time <= start_time) & (ScheduleSlot.end_time > start_time)) |
            ((ScheduleSlot.start_time < end_time) & (ScheduleSlot.end_time >= end_time)) |
            ((ScheduleSlot.start_time >= start_time) & (ScheduleSlot.end_time <= end_time))
        )
    
    if exclude_slot_id:
        conflicting_slots = conflicting_slots.filter(ScheduleSlot.id != exclude_slot_id)
    
    return conflicting_slots.count() == 0