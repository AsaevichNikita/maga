import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import create_app, db
from app.models import Teacher, Course, CourseCategory, ScheduleSlot

app = create_app()

with app.app_context():
    print("📊 ПРОВЕРКА ДАННЫХ В БАЗЕ:")
    
    # Проверяем преподавателей
    teachers = Teacher.query.all()
    print(f"👨‍🏫 Преподавателей: {len(teachers)}")
    for t in teachers:
        print(f"  - ID: {t.id}, {t.lastname} {t.firstname} {t.surname}")
    
    # Проверяем курсы
    courses = Course.query.all()
    print(f"📚 Курсов: {len(courses)}")
    for c in courses:
        print(f"  - ID: {c.id}, {c.name}")
    
    # Проверяем расписание
    schedule = ScheduleSlot.query.all()
    print(f"📅 Слотов расписания: {len(schedule)}")
    for s in schedule:
        print(f"  - ID: {s.id}, Курс: {s.course.name if s.course else None}")
    
    # Если данных нет, создаем демо-данные
    if not teachers:
        print("❌ Данных нет! Создаем демо-данные...")
        from datetime import time, date
        
        teacher = Teacher(
            firstname="Иван",
            lastname="Петров",
            surname="Сергеевич",
            birthday=date(1980, 5, 15),
            email="ivan.petrov@example.com"
        )
        
        category = CourseCategory(name="Математика", description="Курсы по математике")
        course = Course(
            name="Математика для начальной школы",
            description="Основы математики",
            category=category,
            teacher=teacher,
            max_students=15,
            duration_minutes=60,
            is_active=True
        )
        
        schedule_slot = ScheduleSlot(
            course=course,
            day_of_week=1,
            start_time=time(14, 0),
            end_time=time(15, 0),
            classroom="Кабинет 101"
        )
        
        db.session.add_all([teacher, category, course, schedule_slot])
        db.session.commit()
        print("✅ Демо-данные созданы!")