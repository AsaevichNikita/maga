from src.app import db
from sqlalchemy.dialects.postgresql import ARRAY, ENUM
from sqlalchemy import (
    Text, Date, Time, Integer, String, Boolean, Numeric,
    ForeignKey, CheckConstraint, UniqueConstraint, Table
)
from sqlalchemy.orm import relationship


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
    group_name = db.Column(String(50), nullable=False)  # школьный класс/группа
    education_type = db.Column(education_enum, nullable=False)
    enrolled_this_year = db.Column(Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    preferences = relationship('StudentPreference', back_populates='student', cascade='all, delete-orphan')
    registrations = relationship('CourseRegistration', back_populates='student', cascade='all, delete-orphan')
    parent_registrations = relationship('StudentRegistration', back_populates='student', cascade='all, delete-orphan')


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

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    # какие курсы может вести
    allowed_courses = relationship('Course', secondary=course_teachers, back_populates='allowed_teachers')

    # какие группы ведёт как ведущий преподаватель
    lead_groups = relationship('CourseGroup', back_populates='lead_teacher', foreign_keys='CourseGroup.lead_teacher_id')


class Assistant(db.Model):
    """
    Ассистент — отдельная сущность (не Teacher).
    Может быть прикреплён к нескольким группам, но без пересечений по расписанию (проверяется логикой приложения).
    """
    __tablename__ = 'assistants'
    __table_args__ = {'extend_existing': True}

    id = db.Column(Integer, primary_key=True)
    firstname = db.Column(String(100), nullable=False)
    lastname = db.Column(String(100), nullable=False)
    surname = db.Column(String(100))
    birthday = db.Column(Date, nullable=False)

    phone_number = db.Column(String(20), nullable=False)
    email = db.Column(String(100), unique=True)  # может быть NULL

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    groups = relationship('CourseGroup', secondary=group_assistants, back_populates='assistants')


class CourseCategory(db.Model):
    """
    Направление: "Математика 5-7", "Информатика 1-4" и т.д.
    Храним и классы, и возраст (для "юных дарований" и нестандартных кейсов).
    """
    __tablename__ = 'course_categories'
    __table_args__ = {'extend_existing': True}

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), unique=True, nullable=False)
    description = db.Column(Text)

    # Диапазон классов (рекомендуемый)
    min_grade = db.Column(Integer)
    max_grade = db.Column(Integer)

    # Диапазон возраста (рекомендуемый/вспомогательный)
    min_age = db.Column(Integer)
    max_age = db.Column(Integer)

    education_level = db.Column(education_enum)

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    courses = relationship('Course', back_populates='category')


class Course(db.Model):
    """
    Курс = "что именно преподаём" внутри направления:
    например: "Математика базовая", "Олимпиадная математика", "Подготовка к ЕГЭ" и т.д.
    """
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

    # преподаватели, которые вообще могут вести этот курс
    allowed_teachers = relationship('Teacher', secondary=course_teachers, back_populates='allowed_courses')

    # группы курса (каждый учебный год формируются новые)
    groups = relationship('CourseGroup', back_populates='course', cascade='all, delete-orphan')

    # заявки/регистрации на курс
    registrations = relationship('CourseRegistration', back_populates='course', cascade='all, delete-orphan')

    informatics_blocks = relationship('InformaticsBlock', back_populates='course', cascade='all, delete-orphan')

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
    """
    Вспомогательная сущность для информатики:
    блок/трек с перечнем skills, внутри курса.
    Группы можно привязать к блоку (CourseGroup.block_id), чтобы упростить распределение.
    """
    __tablename__ = 'informatics_blocks'
    __table_args__ = {'extend_existing': True}

    id = db.Column(Integer, primary_key=True)
    course_id = db.Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)

    name = db.Column(String(100), nullable=False)
    description = db.Column(Text)

    skills = db.Column(ARRAY(String))  # список тегов/навыков

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    course = relationship('Course', back_populates='informatics_blocks')
    groups = relationship('CourseGroup', back_populates='informatics_block')


class CourseGroup(db.Model):
    """
    Группа = конкретная учебная группа в конкретный учебный год.
    Группа живёт <= 1 года (по твоей логике), затем создаётся новая группа в новом году.
    """
    __tablename__ = 'course_groups'
    __table_args__ = (
        UniqueConstraint('course_id', 'name', 'academic_year', name='uq_group_course_name_year'),
        {'extend_existing': True}
    )

    id = db.Column(Integer, primary_key=True)

    course_id = db.Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)

    # ведущий преподаватель группы (ассистенты отдельно)
    lead_teacher_id = db.Column(Integer, ForeignKey('teachers.id', ondelete='SET NULL'))

    # опционально: привязка к informatics_block (для информатики/треков)
    block_id = db.Column(Integer, ForeignKey('informatics_blocks.id', ondelete='SET NULL'))

    name = db.Column(String(50), nullable=False)          # например "A", "Б", "Группа 1"
    academic_year = db.Column(String(9), nullable=False)  # "2025/2026"
    is_active = db.Column(Boolean, default=True)

    # диапазон уровней 1..10 (для распределения)
    min_level = db.Column(Integer)
    max_level = db.Column(Integer)

    # если нужно переопределить лимит именно для этой группы
    max_students_override = db.Column(Integer)

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    course = relationship('Course', back_populates='groups')
    lead_teacher = relationship('Teacher', back_populates='lead_groups', foreign_keys=[lead_teacher_id])

    assistants = relationship('Assistant', secondary=group_assistants, back_populates='groups')

    # у группы по правилам 1 занятие в неделю → 1 ScheduleSlot (зафиксируем constraint-ом в ScheduleSlot)
    schedule_slot = relationship('ScheduleSlot', back_populates='group', uselist=False, cascade='all, delete-orphan')

    registrations = relationship('CourseRegistration', back_populates='group')

    informatics_block = relationship('InformaticsBlock', back_populates='groups')


class Classroom(db.Model):
    """
    Аудитория / кабинет с указанием вместимости.
    Если course.use_classroom_capacity=True, то лимит мест берём из Classroom.capacity.
    """
    __tablename__ = 'classrooms'
    __table_args__ = {'extend_existing': True}

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(50), unique=True, nullable=False)
    capacity = db.Column(Integer, nullable=False, default=15)

    schedule_slots = relationship('ScheduleSlot', back_populates='classroom')


class ScheduleSlot(db.Model):
    """
    Расписание группы.
    По твоей логике у группы РОВНО 1 занятие в неделю → ставим UniqueConstraint на group_id.
    """
    __tablename__ = 'schedule_slots'
    __table_args__ = (
        CheckConstraint('day_of_week >= 1 AND day_of_week <= 7', name='check_day_of_week'),
        UniqueConstraint('group_id', name='uq_schedule_slot_group'),
        {'extend_existing': True}
    )

    id = db.Column(Integer, primary_key=True)

    group_id = db.Column(Integer, ForeignKey('course_groups.id', ondelete='CASCADE'), nullable=False)

    day_of_week = db.Column(Integer, nullable=False)  # 1..7
    start_time = db.Column(Time, nullable=False)
    end_time = db.Column(Time, nullable=False)

    classroom_id = db.Column(Integer, ForeignKey('classrooms.id', ondelete='SET NULL'))

    group = relationship('CourseGroup', back_populates='schedule_slot')
    classroom = relationship('Classroom', back_populates='schedule_slots')

    # заявки могут хранить "предпочтительный слот"
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


class AssistantSubstitution(db.Model):
    """
    Подмена ассистента на конкретную дату занятия группы (вручную).
    Время занятия берём из ScheduleSlot группы.
    """
    __tablename__ = 'assistant_substitutions'
    __table_args__ = (
        UniqueConstraint('group_id', 'date', 'substitute_assistant_id', name='uq_group_date_substitute'),
        {'extend_existing': True}
    )

    id = db.Column(Integer, primary_key=True)

    group_id = db.Column(Integer, ForeignKey('course_groups.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(Date, nullable=False)

    # кто пришёл
    substitute_assistant_id = db.Column(Integer, ForeignKey('assistants.id', ondelete='CASCADE'), nullable=False)

    # кого заменяет (NULL = добавился дополнительно)
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

    # можно хранить подобранные курсы (как было)
    matched_courses = db.Column(ARRAY(Integer))

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    student = relationship('Student', back_populates='preferences')
    registrations = relationship('CourseRegistration', back_populates='preference')


class CourseRegistration(db.Model):
    """
    Заявка/регистрация студента.

    Важные моменты по твоей логике:
    - студент может выбрать курс (course_id) ИЛИ сотрудники могут назначить course_id позже
      (например, в информатике "как карта ляжет")
    - после назначения course_id нельзя записаться на этот же курс снова (в базе это UniqueConstraint)
    - группа (group_id) назначается позже, после формирования расписания/распределения
    - студент указывает level 1..10 и может выбрать предпочтительный слот (preferred_slot_id)
    """
    __tablename__ = 'course_registrations'
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'rejected', 'completed')", name='check_status'),
        CheckConstraint("level IS NULL OR (level >= 1 AND level <= 10)", name='check_level_1_10'),
        UniqueConstraint('student_id', 'course_id', name='uq_student_course_once'),
        {'extend_existing': True}
    )

    id = db.Column(Integer, primary_key=True)

    student_id = db.Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)

    # курс может быть назначен позже (для информатики/распределения)
    course_id = db.Column(Integer, ForeignKey('courses.id', ondelete='SET NULL'))

    # выбранное направление (полезно, если курс пока не назначен)
    category_id = db.Column(Integer, ForeignKey('course_categories.id', ondelete='SET NULL'))

    # группа назначается позже
    group_id = db.Column(Integer, ForeignKey('course_groups.id', ondelete='SET NULL'))

    # предпочтительный слот (какое время удобно)
    preferred_slot_id = db.Column(Integer, ForeignKey('schedule_slots.id', ondelete='SET NULL'))

    # опционально: в информатике можно хранить выбранный блок/трек
    block_id = db.Column(Integer, ForeignKey('informatics_blocks.id', ondelete='SET NULL'))

    # пожелания/комментарии (в т.ч. "хочу к этому преподу", "хочу такой курс")
    comment = db.Column(Text)

    # уровень ученика 1..10
    level = db.Column(Integer)

    # если нужно — навыки (для информатики)
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