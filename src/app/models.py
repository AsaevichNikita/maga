from __future__ import annotations

from src.app import db
from sqlalchemy.dialects.postgresql import ARRAY, ENUM
from sqlalchemy import (
    Text, Date, Time, Integer, String, Boolean, Numeric,
    ForeignKey, CheckConstraint, UniqueConstraint, Table
)
from sqlalchemy.orm import relationship


def parse_academic_year(value: str) -> tuple[int, int]:
    if not value:
        raise ValueError('academic_year is required')

    normalized = value.strip().replace('-', '/')
    parts = normalized.split('/')

    if len(parts) != 2:
        raise ValueError('academic_year must be in format YYYY/YYYY or YYYY-YYYY')

    start = int(parts[0])
    end = int(parts[1])

    if end != start + 1:
        raise ValueError('academic_year_end must be academic_year_start + 1')

    return start, end


# ------------------------
# PostgreSQL ENUM
# ------------------------
education_enum = ENUM(
    'дошкольное',
    'школьное',
    'среднее_профессиональное',
    'высшее',
    name='education_type',
    create_type=True
)


# ------------------------
# Связь: какие преподаватели могут вести курс (Course <-> Teacher)
# ------------------------
course_teachers = Table(
    'course_teachers',
    db.Model.metadata,
    db.Column('course_id', Integer, ForeignKey('courses.id', ondelete='CASCADE'), primary_key=True),
    db.Column('teacher_id', Integer, ForeignKey('teachers.id', ondelete='CASCADE'), primary_key=True),
)


# ------------------------
# Связь: ассистенты группы (CourseGroup <-> Assistant)
# ------------------------
group_assistants = Table(
    'group_assistants',
    db.Model.metadata,
    db.Column('group_id', Integer, ForeignKey('course_groups.id', ondelete='CASCADE'), primary_key=True),
    db.Column('assistant_id', Integer, ForeignKey('assistants.id', ondelete='CASCADE'), primary_key=True),
)


# ============================================================
# Основные сущности
# ============================================================

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

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    preferences = relationship('StudentPreference', back_populates='student', cascade='all, delete-orphan')
    registrations = relationship('CourseRegistration', back_populates='student', cascade='all, delete-orphan')
    parent_registrations = relationship('StudentRegistration', back_populates='student', cascade='all, delete-orphan')


class Parent(db.Model):
    __tablename__ = 'parents'
    __table_args__ = {'extend_existing': True}

    keycloak_user_id = db.Column(String(64), unique=True, index=True)
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

    keycloak_user_id = db.Column(String(64), unique=True, index=True)
    id = db.Column(Integer, primary_key=True)
    firstname = db.Column(String(100), nullable=False)
    lastname = db.Column(String(100), nullable=False)
    surname = db.Column(String(100))
    birthday = db.Column(Date, nullable=False)
    phone_number = db.Column(String(20))
    email = db.Column(String(100), unique=True, nullable=False)

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    allowed_courses = relationship('Course', secondary=course_teachers, back_populates='allowed_teachers')
    lead_groups = relationship('CourseGroup', back_populates='lead_teacher', foreign_keys='CourseGroup.lead_teacher_id')
    offering_slots = relationship('TeacherOfferingSlot', back_populates='teacher', cascade='all, delete-orphan')


class Assistant(db.Model):
    __tablename__ = 'assistants'
    __table_args__ = {'extend_existing': True}

    keycloak_user_id = db.Column(String(64), unique=True, index=True)
    id = db.Column(Integer, primary_key=True)
    firstname = db.Column(String(100), nullable=False)
    lastname = db.Column(String(100), nullable=False)
    surname = db.Column(String(100))
    birthday = db.Column(Date, nullable=False)

    phone_number = db.Column(String(20), nullable=False)
    email = db.Column(String(100), unique=True)

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    groups = relationship('CourseGroup', secondary=group_assistants, back_populates='assistants')


class CourseCategory(db.Model):
    __tablename__ = 'course_categories'
    __table_args__ = {'extend_existing': True}

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), unique=True, nullable=False)
    description = db.Column(Text)

    min_grade = db.Column(Integer)
    max_grade = db.Column(Integer)

    min_age = db.Column(Integer)
    max_age = db.Column(Integer)

    education_level = db.Column(education_enum)

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    courses = relationship('Course', back_populates='category')


class Course(db.Model):
    __tablename__ = 'courses'
    __table_args__ = {'extend_existing': True}

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False)
    description = db.Column(Text)

    category_id = db.Column(Integer, ForeignKey('course_categories.id', ondelete='SET NULL'))

    max_students = db.Column(Integer, nullable=False, default=15)
    use_classroom_capacity = db.Column(Boolean, nullable=False, default=False)
    duration_minutes = db.Column(Integer, nullable=False, default=90)
    price = db.Column(Numeric(10, 2))
    is_active = db.Column(Boolean, default=True)

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    category = relationship('CourseCategory', back_populates='courses')
    allowed_teachers = relationship('Teacher', secondary=course_teachers, back_populates='allowed_courses')
    groups = relationship('CourseGroup', back_populates='course', cascade='all, delete-orphan')
    registrations = relationship('CourseRegistration', back_populates='course', cascade='all, delete-orphan')
    informatics_blocks = relationship('InformaticsBlock', back_populates='course', cascade='all, delete-orphan')
    offering_slots = relationship('TeacherOfferingSlot', back_populates='course', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id,
            'category': self.category.name if self.category else None,
            'max_students': self.max_students,
            'use_classroom_capacity': self.use_classroom_capacity,
            'duration_minutes': self.duration_minutes,
            'price': float(self.price) if self.price else None,
            'is_active': self.is_active
        }


class InformaticsBlock(db.Model):
    __tablename__ = 'informatics_blocks'
    __table_args__ = {'extend_existing': True}

    id = db.Column(Integer, primary_key=True)
    course_id = db.Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)

    name = db.Column(String(100), nullable=False)
    description = db.Column(Text)

    skills = db.Column(ARRAY(String))

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    course = relationship('Course', back_populates='informatics_blocks')
    groups = relationship('CourseGroup', back_populates='informatics_block')


class CourseGroup(db.Model):
    __tablename__ = 'course_groups'
    __table_args__ = (
        UniqueConstraint(
            'course_id', 'name', 'academic_year_start', 'academic_year_end',
            name='uq_group_course_name_year'
        ),
        CheckConstraint(
            'academic_year_end = academic_year_start + 1',
            name='check_group_academic_year'
        ),
        {'extend_existing': True}
    )

    id = db.Column(Integer, primary_key=True)

    course_id = db.Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    lead_teacher_id = db.Column(Integer, ForeignKey('teachers.id', ondelete='SET NULL'))
    block_id = db.Column(Integer, ForeignKey('informatics_blocks.id', ondelete='SET NULL'))

    source_offering_slot_id = db.Column(Integer, ForeignKey('teacher_offering_slots.id', ondelete='SET NULL'))

    name = db.Column(String(50), nullable=False)

    academic_year_start = db.Column(Integer, nullable=False)
    academic_year_end = db.Column(Integer, nullable=False)

    is_active = db.Column(Boolean, default=True)

    min_level = db.Column(Integer)
    max_level = db.Column(Integer)

    max_students_override = db.Column(Integer)

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    course = relationship('Course', back_populates='groups')
    lead_teacher = relationship('Teacher', back_populates='lead_groups', foreign_keys=[lead_teacher_id])

    assistants = relationship('Assistant', secondary=group_assistants, back_populates='groups')

    schedule_slot = relationship('ScheduleSlot', back_populates='group', uselist=False, cascade='all, delete-orphan')

    registrations = relationship('CourseRegistration', back_populates='group')

    informatics_block = relationship('InformaticsBlock', back_populates='groups')

    source_offering_slot = relationship(
        'TeacherOfferingSlot',
        back_populates='created_groups',
        foreign_keys=[source_offering_slot_id]
    )

    @property
    def academic_year(self) -> str | None:
        if self.academic_year_start is None or self.academic_year_end is None:
            return None
        return f'{self.academic_year_start}/{self.academic_year_end}'

    @academic_year.setter
    def academic_year(self, value: str) -> None:
        start, end = parse_academic_year(value)
        self.academic_year_start = start
        self.academic_year_end = end


class Classroom(db.Model):
    __tablename__ = 'classrooms'
    __table_args__ = {'extend_existing': True}

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(50), unique=True, nullable=False)
    capacity = db.Column(Integer, nullable=False, default=15)

    schedule_slots = relationship('ScheduleSlot', back_populates='classroom')
    offering_slots = relationship('TeacherOfferingSlot', back_populates='classroom')


class ScheduleSlot(db.Model):
    __tablename__ = 'schedule_slots'
    __table_args__ = (
        CheckConstraint('day_of_week >= 1 AND day_of_week <= 7', name='check_day_of_week'),
        CheckConstraint('end_time > start_time', name='check_schedule_time_range'),
        UniqueConstraint('group_id', name='uq_schedule_slot_group'),
        {'extend_existing': True}
    )

    id = db.Column(Integer, primary_key=True)

    group_id = db.Column(Integer, ForeignKey('course_groups.id', ondelete='CASCADE'), nullable=False)

    day_of_week = db.Column(Integer, nullable=False)
    start_time = db.Column(Time, nullable=False)
    end_time = db.Column(Time, nullable=False)

    classroom_id = db.Column(Integer, ForeignKey('classrooms.id', ondelete='SET NULL'))

    group = relationship('CourseGroup', back_populates='schedule_slot')
    classroom = relationship('Classroom', back_populates='schedule_slots')

    registrations = relationship('CourseRegistration', back_populates='preferred_slot')

    def to_dict(self):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'course_id': self.group.course_id if self.group else None,
            'course_name': self.group.course.name if self.group and self.group.course else None,
            'group_name': self.group.name if self.group else None,
            'academic_year': self.group.academic_year if self.group else None,
            'lead_teacher': (
                f"{self.group.lead_teacher.lastname} {self.group.lead_teacher.firstname}"
                if self.group and self.group.lead_teacher else None
            ),
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M'),
            'classroom': self.classroom.name if self.classroom else None,
            'classroom_capacity': self.classroom.capacity if self.classroom else None,
        }


class TeacherOfferingSlot(db.Model):
    """
    Слот набора:
    преподаватель заранее публикует, что готов вести конкретный курс
    в конкретное время в конкретном учебном году.
    Именно эти слоты видят регистрирующиеся дети в заявке.
    """
    __tablename__ = 'teacher_offering_slots'
    __table_args__ = (
        CheckConstraint('day_of_week >= 1 AND day_of_week <= 7', name='check_offering_day_of_week'),
        CheckConstraint('max_groups >= 1', name='check_offering_max_groups'),
        CheckConstraint('end_time > start_time', name='check_offering_time_range'),
        CheckConstraint(
            'academic_year_end = academic_year_start + 1',
            name='check_offering_academic_year'
        ),
        UniqueConstraint(
            'teacher_id', 'course_id', 'academic_year_start', 'academic_year_end',
            'day_of_week', 'start_time', 'end_time',
            name='uq_teacher_course_year_time'
        ),
        {'extend_existing': True}
    )

    id = db.Column(Integer, primary_key=True)

    teacher_id = db.Column(Integer, ForeignKey('teachers.id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)

    academic_year_start = db.Column(Integer, nullable=False)
    academic_year_end = db.Column(Integer, nullable=False)

    day_of_week = db.Column(Integer, nullable=False)
    start_time = db.Column(Time, nullable=False)
    end_time = db.Column(Time, nullable=False)

    classroom_id = db.Column(Integer, ForeignKey('classrooms.id', ondelete='SET NULL'))

    is_active = db.Column(Boolean, nullable=False, default=True)

    max_groups = db.Column(Integer, nullable=False, default=1)
    priority = db.Column(Integer, nullable=False, default=100)

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    teacher = relationship('Teacher', back_populates='offering_slots')
    course = relationship('Course', back_populates='offering_slots')
    classroom = relationship('Classroom', back_populates='offering_slots')

    registration_preferences = relationship(
        'RegistrationSlotPreference',
        back_populates='offering_slot',
        cascade='all, delete-orphan'
    )

    created_groups = relationship(
        'CourseGroup',
        back_populates='source_offering_slot',
        foreign_keys='CourseGroup.source_offering_slot_id'
    )

    @property
    def academic_year(self) -> str | None:
        if self.academic_year_start is None or self.academic_year_end is None:
            return None
        return f'{self.academic_year_start}/{self.academic_year_end}'

    @academic_year.setter
    def academic_year(self, value: str) -> None:
        start, end = parse_academic_year(value)
        self.academic_year_start = start
        self.academic_year_end = end

    def to_dict(self):
        return {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'teacher_name': (
                f"{self.teacher.lastname} {self.teacher.firstname} {self.teacher.surname or ''}".strip()
                if self.teacher else None
            ),
            'course_id': self.course_id,
            'course_name': self.course.name if self.course else None,
            'academic_year': self.academic_year,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M'),
            'classroom_id': self.classroom_id,
            'classroom_name': self.classroom.name if self.classroom else None,
            'classroom_capacity': self.classroom.capacity if self.classroom else None,
            'is_active': self.is_active,
            'max_groups': self.max_groups,
            'priority': self.priority,
        }


class AssistantSubstitution(db.Model):
    __tablename__ = 'assistant_substitutions'
    __table_args__ = (
        UniqueConstraint('group_id', 'date', 'substitute_assistant_id', name='uq_group_date_substitute'),
        {'extend_existing': True}
    )

    id = db.Column(Integer, primary_key=True)

    group_id = db.Column(Integer, ForeignKey('course_groups.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(Date, nullable=False)

    substitute_assistant_id = db.Column(Integer, ForeignKey('assistants.id', ondelete='CASCADE'), nullable=False)
    replaced_assistant_id = db.Column(Integer, ForeignKey('assistants.id', ondelete='SET NULL'))

    note = db.Column(Text)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    group = relationship('CourseGroup')
    substitute = relationship('Assistant', foreign_keys=[substitute_assistant_id])
    replaced = relationship('Assistant', foreign_keys=[replaced_assistant_id])


# ============================================================
# Заявки / регистрации / пожелания
# ============================================================

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
        CheckConstraint("status IN ('pending', 'approved', 'rejected', 'completed')", name='check_status'),
        CheckConstraint("level IS NULL OR (level >= 1 AND level <= 10)", name='check_level_1_10'),
        UniqueConstraint('student_id', 'course_id', name='uq_student_course_once'),
        {'extend_existing': True}
    )

    id = db.Column(Integer, primary_key=True)

    student_id = db.Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(Integer, ForeignKey('courses.id', ondelete='SET NULL'))
    category_id = db.Column(Integer, ForeignKey('course_categories.id', ondelete='SET NULL'))
    group_id = db.Column(Integer, ForeignKey('course_groups.id', ondelete='SET NULL'))

    preferred_slot_id = db.Column(Integer, ForeignKey('schedule_slots.id', ondelete='SET NULL'))

    block_id = db.Column(Integer, ForeignKey('informatics_blocks.id', ondelete='SET NULL'))

    comment = db.Column(Text)
    level = db.Column(Integer)
    skills = db.Column(ARRAY(String))

    preference_id = db.Column(Integer, ForeignKey('student_preferences.id'))

    status = db.Column(String(20), default='pending')

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    completed_at = db.Column(db.DateTime(timezone=True))

    student = relationship('Student', back_populates='registrations')
    course = relationship('Course', back_populates='registrations')
    category = relationship('CourseCategory')
    group = relationship('CourseGroup', back_populates='registrations')
    preferred_slot = relationship('ScheduleSlot', back_populates='registrations')
    preference = relationship('StudentPreference', back_populates='registrations')
    block = relationship('InformaticsBlock')

    slot_preferences = relationship(
        'RegistrationSlotPreference',
        back_populates='registration',
        cascade='all, delete-orphan'
    )


class RegistrationSlotPreference(db.Model):
    """
    Предпочтения ребёнка по published/offering slots в рамках одной заявки.
    priority: 1 = самый желаемый слот.
    """
    __tablename__ = 'registration_slot_preferences'
    __table_args__ = (
        CheckConstraint('priority >= 1', name='check_slot_preference_priority'),
        UniqueConstraint('registration_id', 'offering_slot_id', name='uq_registration_offering_slot'),
        UniqueConstraint('registration_id', 'priority', name='uq_registration_slot_priority'),
        {'extend_existing': True}
    )

    id = db.Column(Integer, primary_key=True)

    registration_id = db.Column(Integer, ForeignKey('course_registrations.id', ondelete='CASCADE'), nullable=False)
    offering_slot_id = db.Column(Integer, ForeignKey('teacher_offering_slots.id', ondelete='CASCADE'), nullable=False)

    priority = db.Column(Integer, nullable=False, default=1)

    registration = relationship('CourseRegistration', back_populates='slot_preferences')
    offering_slot = relationship('TeacherOfferingSlot', back_populates='registration_preferences')

    def to_dict(self):
        return {
            'id': self.id,
            'registration_id': self.registration_id,
            'offering_slot_id': self.offering_slot_id,
            'priority': self.priority,
            'offering_slot': self.offering_slot.to_dict() if self.offering_slot else None
        }


class StudentRegistration(db.Model):
    __tablename__ = 'student_registrations'
    __table_args__ = {'extend_existing': True}

    id = db.Column(Integer, primary_key=True)
    student_id = db.Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    parent_id = db.Column(Integer, ForeignKey('parents.id', ondelete='CASCADE'), nullable=False)

    student = relationship('Student', back_populates='parent_registrations')
    parent = relationship('Parent', back_populates='student_registrations')


class ReservedTime(db.Model):
    """
    Если хочешь оставить как общую таблицу "зарезервированных/запрещённых" интервалов,
    можно оставить. Но в логике аллокации по новым published slots она уже не основная.
    """
    __tablename__ = 'reserved_times'
    __table_args__ = (
        CheckConstraint('day_of_week >= 1 AND day_of_week <= 7', name='check_reserved_day'),
        CheckConstraint('end_time > start_time', name='check_reserved_time_range'),
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