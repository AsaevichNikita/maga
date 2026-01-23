from src.app import db
from sqlalchemy.dialects.postgresql import ARRAY, ENUM
from sqlalchemy import (
    Text, Date, Time, Integer, String, Boolean, Numeric,
    ForeignKey, CheckConstraint, UniqueConstraint, Table
)
from sqlalchemy.orm import relationship
from datetime import datetime

# ENUM тип для PostgreSQL
education_enum = ENUM(
    'дошкольное', 
    'школьное', 
    'среднее_профессиональное', 
    'высшее',
    name='education_type',
    create_type=True
)

# ------------------------
# Таблица связи many-to-many между студентами и курсами
# ------------------------
course_students = Table(
    'course_students',
    db.Model.metadata,
    db.Column('student_id', Integer, ForeignKey('students.id', ondelete='CASCADE'), primary_key=True),
    db.Column('course_id', Integer, ForeignKey('courses.id', ondelete='CASCADE'), primary_key=True),
    extend_existing=True
)

# ------------------------
# Остальные модели
# ------------------------
class Student(db.Model):
    __tablename__ = 'students'
    __table_args__ = {'extend_existing': True} 

    id = db.Column(Integer, primary_key=True)
    firstname = db.Column(String(100), nullable=False)
    lastname = db.Column(String(100), nullable=False)
    surname = db.Column(String(100))
    phone_number = db.Column(String(20))
    email = db.Column(String(100))
    birthday = db.Column(Date, nullable=False)
    address = db.Column(String(200), nullable=False)
    educational_institution = db.Column(String(100), nullable=False)
    group_name = db.Column(String(50), nullable=False)
    education_type = db.Column(education_enum, nullable=False)
    enrolled_this_year = db.Column(Boolean, nullable=False, default=False)

    preferences = relationship('StudentPreference', back_populates='student', cascade='all, delete-orphan')
    registrations = relationship('CourseRegistration', back_populates='student', cascade='all, delete-orphan')
    parent_registrations = relationship('StudentRegistration', back_populates='student', cascade='all, delete-orphan')
    courses = relationship('Course', secondary=course_students, back_populates='students')


class Parent(db.Model):
    __tablename__ = 'parents'
    __table_args__ = {'extend_existing': True} 

    id = db.Column(Integer, primary_key=True)
    firstname = db.Column(String(100), nullable=False)
    lastname = db.Column(String(100), nullable=False)
    surname = db.Column(String(100))
    birthday = db.Column(Date, nullable=False)
    address = db.Column(String(200), nullable=False)
    phone_number = db.Column(String(20))
    email = db.Column(String(100), unique=True, nullable=False)
    data_processing_consent = db.Column(Boolean, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    student_registrations = relationship('StudentRegistration', back_populates='parent')


class Teacher(db.Model):
    __tablename__ = 'teachers'
    __table_args__ = {'extend_existing': True} 

    id = db.Column(Integer, primary_key=True)
    firstname = db.Column(String(100), nullable=False)
    lastname = db.Column(String(100), nullable=False)
    surname = db.Column(String(100))
    birthday = db.Column(Date, nullable=False)
    phone_number = db.Column(String(20))
    email = db.Column(String(100), unique=True, nullable=False)

    courses = relationship('Course', back_populates='teacher')
    schedule_slots = relationship('ScheduleSlot', back_populates='teacher')


class CourseCategory(db.Model):
    __tablename__ = 'course_categories'
    __table_args__ = {'extend_existing': True} 

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), unique=True, nullable=False)
    description = db.Column(Text)
    min_age = db.Column(Integer)
    max_age = db.Column(Integer)
    education_level = db.Column(education_enum)

    courses = relationship('Course', back_populates='category')


class Course(db.Model):
    __tablename__ = 'courses'
    __table_args__ = {'extend_existing': True} 

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False)
    description = db.Column(Text)
    category_id = db.Column(Integer, ForeignKey('course_categories.id', ondelete='SET NULL'))
    teacher_id = db.Column(Integer, ForeignKey('teachers.id', ondelete='SET NULL'))
    max_students = db.Column(Integer, nullable=False, default=15)
    # если True — максимум учеников для этого курса определяется вместимостью аудитории
    use_classroom_capacity = db.Column(Boolean, nullable=False, default=False)
    duration_minutes = db.Column(Integer, nullable=False, default=90)
    price = db.Column(Numeric(10, 2))
    is_active = db.Column(Boolean, default=True)

    category = relationship('CourseCategory', back_populates='courses')
    teacher = relationship('Teacher', back_populates='courses')
    schedule_slots = relationship('ScheduleSlot', back_populates='course', cascade='all, delete-orphan', passive_deletes=True)
    registrations = relationship('CourseRegistration', back_populates='course', cascade='all, delete-orphan', passive_deletes=True)
    students = relationship('Student', secondary=course_students, back_populates='courses')
    informatics_blocks = relationship('InformaticsBlock', back_populates='course', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category.name if self.category else None,
            'teacher': f"{self.teacher.lastname} {self.teacher.firstname}" if self.teacher else None,
            'max_students': self.max_students,
            'use_classroom_capacity': self.use_classroom_capacity,
            'duration_minutes': self.duration_minutes,
            'price': float(self.price) if self.price else None,
            'is_active': self.is_active
        }


class Classroom(db.Model):
    """
    Аудитория / кабинет с указанием вместимости.
    Для информатики максимум учеников определяется вместимостью этой аудитории.
    """
    __tablename__ = 'classrooms'
    __table_args__ = {'extend_existing': True}

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(50), unique=True, nullable=False)
    capacity = db.Column(Integer, nullable=False, default=15)

    schedule_slots = relationship('ScheduleSlot', back_populates='classroom')


class InformaticsBlock(db.Model):
    """
    'Крупный блок' для групп информатики.
    Внутри блока студент выбирает только слот (время), при регистрации указывает навыки.
    """
    __tablename__ = 'informatics_blocks'
    __table_args__ = {'extend_existing': True}

    id = db.Column(Integer, primary_key=True)
    course_id = db.Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(String(100), nullable=False)
    description = db.Column(Text)
    # список навыков/тегов, которые студент указывает при регистрации в этом блоке
    skills = db.Column(ARRAY(String))
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    course = relationship('Course', back_populates='informatics_blocks')
    schedule_slots = relationship('ScheduleSlot', back_populates='block', cascade='all, delete-orphan')


class ScheduleSlot(db.Model):
    __tablename__ = 'schedule_slots'
    __table_args__ = (
        CheckConstraint('day_of_week >= 1 AND day_of_week <= 7', name='check_day_of_week'),
        {'extend_existing': True}
    )

    id = db.Column(Integer, primary_key=True)
    course_id = db.Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    teacher_id = db.Column(Integer, ForeignKey('teachers.id', ondelete='CASCADE'), nullable=False)
    day_of_week = db.Column(Integer, nullable=False)
    start_time = db.Column(Time, nullable=False)
    end_time = db.Column(Time, nullable=False)

    # привязка слота к конкретной аудитории
    classroom_id = db.Column(Integer, ForeignKey('classrooms.id', ondelete='SET NULL'))
    # опционально: слот может принадлежать информатическому блоку
    block_id = db.Column(Integer, ForeignKey('informatics_blocks.id', ondelete='CASCADE'))

    course = relationship('Course', back_populates='schedule_slots')
    teacher = relationship('Teacher', back_populates='schedule_slots')
    classroom = relationship('Classroom', back_populates='schedule_slots')
    block = relationship('InformaticsBlock', back_populates='schedule_slots')
    registrations = relationship('CourseRegistration', back_populates='slot', cascade='all, delete-orphan', passive_deletes=True)

    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'course_name': self.course.name if self.course else None,
            'teacher_name': f"{self.course.teacher.lastname} {self.course.teacher.firstname}" if self.course and self.course.teacher else None,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M'),
            'classroom': self.classroom.name if self.classroom else None,
            'classroom_capacity': self.classroom.capacity if self.classroom else None,
            'block_id': self.block_id
        }


class StudentPreference(db.Model):
    __tablename__ = 'student_preferences'
    __table_args__ = {'extend_existing': True} 

    id = db.Column(Integer, primary_key=True)
    student_id = db.Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    preference_text = db.Column(Text, nullable=False)
    processed = db.Column(Boolean, default=False)
    matched_courses = db.Column(ARRAY(Integer))
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    student = relationship('Student', back_populates='preferences')
    registrations = relationship('CourseRegistration', back_populates='preference')


class CourseRegistration(db.Model):
    __tablename__ = 'course_registrations'
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'rejected')", name='check_status'),
        UniqueConstraint('student_id', 'course_id', name='unique_student_course'),
        {'extend_existing': True}
    )

    id = db.Column(Integer, primary_key=True)
    student_id = db.Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    # если регистрация для информатики — привязка к блоку
    block_id = db.Column(Integer, ForeignKey('informatics_blocks.id', ondelete='SET NULL'))
    schedule_slot_id = db.Column(Integer, ForeignKey('schedule_slots.id', ondelete='CASCADE'))
    preference_id = db.Column(Integer, ForeignKey('student_preferences.id'))
    status = db.Column(String(20), default='pending')
    # Skills/уровень, которые студент указывает при записи на информатику
    skills = db.Column(ARRAY(String))
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    student = relationship('Student', back_populates='registrations')
    course = relationship('Course', back_populates='registrations')
    slot = relationship('ScheduleSlot', back_populates='registrations')
    preference = relationship('StudentPreference', back_populates='registrations')
    block = relationship('InformaticsBlock')


class StudentRegistration(db.Model):
    __tablename__ = 'student_registrations'
    __table_args__ = {'extend_existing': True} 

    id = db.Column(Integer, primary_key=True)
    student_id = db.Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    parent_id = db.Column(Integer, ForeignKey('parents.id', ondelete='CASCADE'), nullable=False)

    student = relationship('Student', back_populates='parent_registrations')
    parent = relationship('Parent', back_populates='student_registrations')


class ReservedTime(db.Model):
    __tablename__ = 'reserved_times'
    __table_args__ = (
        CheckConstraint('day_of_week >= 1 AND day_of_week <= 7', name='check_reserved_day'),
        {'extend_existing': True}
    )

    id = db.Column(Integer, primary_key=True)
    day_of_week = db.Column(Integer, nullable=False)
    start_time = db.Column(Time, nullable=False)
    end_time = db.Column(Time, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M')
        }






