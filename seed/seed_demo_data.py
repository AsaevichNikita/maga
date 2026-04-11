import json
from pathlib import Path
from datetime import datetime

from src.app import create_app, db
from src.app.models import (
    Teacher,
    Assistant,
    Classroom,
    CourseCategory,
    Course,
    Student,
    Parent,
    TeacherOfferingSlot,
    StudentRegistration,
    CourseRegistration,
    RegistrationSlotPreference,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def load_json(filename):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_date(value: str):
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_time(value: str):
    return datetime.strptime(value, "%H:%M").time()


def get_or_create_teacher(item):
    obj = Teacher.query.filter_by(email=item["email"]).first()
    if obj:
        return obj
    obj = Teacher(
        firstname=item["firstname"],
        lastname=item["lastname"],
        surname=item.get("surname"),
        birthday=parse_date(item["birthday"]),
        phone_number=item.get("phone_number"),
        email=item["email"],
    )
    db.session.add(obj)
    db.session.flush()
    return obj


def get_or_create_assistant(item):
    obj = Assistant.query.filter_by(email=item["email"]).first()
    if obj:
        return obj
    obj = Assistant(
        firstname=item["firstname"],
        lastname=item["lastname"],
        surname=item.get("surname"),
        birthday=parse_date(item["birthday"]),
        phone_number=item["phone_number"],
        email=item.get("email"),
    )
    db.session.add(obj)
    db.session.flush()
    return obj


def get_or_create_classroom(item):
    obj = Classroom.query.filter_by(name=item["name"]).first()
    if obj:
        return obj
    obj = Classroom(name=item["name"], capacity=item.get("capacity", 15))
    db.session.add(obj)
    db.session.flush()
    return obj


def get_or_create_category(item):
    obj = CourseCategory.query.filter_by(name=item["name"]).first()
    if obj:
        return obj
    obj = CourseCategory(
        name=item["name"],
        description=item.get("description"),
        min_grade=item.get("min_grade"),
        max_grade=item.get("max_grade"),
        min_age=item.get("min_age"),
        max_age=item.get("max_age"),
        education_level=item.get("education_level"),
    )
    db.session.add(obj)
    db.session.flush()
    return obj


def get_or_create_course(item):
    obj = Course.query.filter_by(name=item["name"]).first()
    if obj:
        return obj

    category = CourseCategory.query.filter_by(name=item["category_name"]).first()
    if not category:
        raise ValueError(f"Category not found: {item['category_name']}")

    obj = Course(
        name=item["name"],
        description=item.get("description"),
        category_id=category.id,
        max_students=item.get("max_students", 15),
        use_classroom_capacity=item.get("use_classroom_capacity", False),
        duration_minutes=item.get("duration_minutes", 90),
        price=item.get("price"),
        is_active=item.get("is_active", True),
    )

    teacher_emails = item.get("allowed_teacher_emails", [])
    if teacher_emails:
        teachers = Teacher.query.filter(Teacher.email.in_(teacher_emails)).all()
        obj.allowed_teachers = teachers

    db.session.add(obj)
    db.session.flush()
    return obj


def get_or_create_student(item):
    obj = Student.query.filter_by(email=item["email"]).first()
    if obj:
        return obj
    obj = Student(
        firstname=item["firstname"],
        lastname=item["lastname"],
        surname=item.get("surname"),
        phone_number=item.get("phone_number"),
        email=item.get("email"),
        birthday=parse_date(item["birthday"]),
        address=item["address"],
        educational_institution=item["educational_institution"],
        group_name=item["group_name"],
        education_type=item["education_type"],
        enrolled_this_year=item.get("enrolled_this_year", False),
    )
    db.session.add(obj)
    db.session.flush()
    return obj


def get_or_create_parent(item):
    obj = Parent.query.filter_by(email=item["email"]).first()
    if obj:
        return obj
    obj = Parent(
        firstname=item["firstname"],
        lastname=item["lastname"],
        surname=item.get("surname"),
        birthday=parse_date(item["birthday"]),
        address=item["address"],
        phone_number=item.get("phone_number"),
        email=item["email"],
        data_processing_consent=item.get("data_processing_consent", True),
    )
    db.session.add(obj)
    db.session.flush()
    return obj


def get_or_create_student_registration(item):
    student = Student.query.filter_by(email=item["student_email"]).first()
    parent = Parent.query.filter_by(email=item["parent_email"]).first()
    if not student or not parent:
        raise ValueError(f"Student or parent not found for link: {item}")

    obj = StudentRegistration.query.filter_by(student_id=student.id, parent_id=parent.id).first()
    if obj:
        return obj

    obj = StudentRegistration(student_id=student.id, parent_id=parent.id)
    db.session.add(obj)
    db.session.flush()
    return obj


def get_or_create_teacher_offering_slot(item):
    teacher = Teacher.query.filter_by(email=item["teacher_email"]).first()
    if not teacher:
        raise ValueError(f"Teacher not found: {item['teacher_email']}")

    course = Course.query.filter_by(name=item["course_name"]).first()
    if not course:
        raise ValueError(f"Course not found: {item['course_name']}")

    classroom = Classroom.query.filter_by(name=item["classroom_name"]).first()
    if not classroom:
        raise ValueError(f"Classroom not found: {item['classroom_name']}")

    start_year, end_year = item["academic_year"].replace("-", "/").split("/")
    start_year = int(start_year)
    end_year = int(end_year)

    obj = TeacherOfferingSlot.query.filter_by(
        teacher_id=teacher.id,
        course_id=course.id,
        academic_year_start=start_year,
        academic_year_end=end_year,
        day_of_week=item["day_of_week"],
        start_time=parse_time(item["start_time"]),
        end_time=parse_time(item["end_time"]),
    ).first()
    if obj:
        return obj

    obj = TeacherOfferingSlot(
        teacher_id=teacher.id,
        course_id=course.id,
        academic_year_start=start_year,
        academic_year_end=end_year,
        day_of_week=item["day_of_week"],
        start_time=parse_time(item["start_time"]),
        end_time=parse_time(item["end_time"]),
        classroom_id=classroom.id,
        is_active=item.get("is_active", True),
        max_groups=item.get("max_groups", 1),
        priority=item.get("priority", 100),
    )
    db.session.add(obj)
    db.session.flush()
    return obj


def find_offering_slot(pref):
    teacher = Teacher.query.filter_by(email=pref["teacher_email"]).first()
    course = Course.query.filter_by(name=pref["course_name"]).first()
    if not teacher or not course:
        return None

    start_year, end_year = pref["academic_year"].replace("-", "/").split("/")
    return TeacherOfferingSlot.query.filter_by(
        teacher_id=teacher.id,
        course_id=course.id,
        academic_year_start=int(start_year),
        academic_year_end=int(end_year),
        day_of_week=pref["day_of_week"],
        start_time=parse_time(pref["start_time"]),
        end_time=parse_time(pref["end_time"]),
    ).first()


def get_or_create_course_registration(item):
    student = Student.query.filter_by(email=item["student_email"]).first()
    if not student:
        raise ValueError(f"Student not found: {item['student_email']}")

    course = Course.query.filter_by(name=item["course_name"]).first()
    if not course:
        raise ValueError(f"Course not found: {item['course_name']}")

    obj = CourseRegistration.query.filter_by(
        student_id=student.id,
        course_id=course.id
    ).first()

    if not obj:
        obj = CourseRegistration(
            student_id=student.id,
            course_id=course.id,
            category_id=course.category_id,
            comment=item.get("comment"),
            level=item.get("level"),
            skills=item.get("skills") or [],
            status=item.get("status", "pending"),
        )
        db.session.add(obj)
        db.session.flush()

    existing_prefs = {p.priority: p for p in obj.slot_preferences}
    for pref in item.get("slot_preferences", []):
        slot = find_offering_slot(pref)
        if not slot:
            continue

        priority = pref["priority"]
        if priority in existing_prefs:
            continue

        pref_obj = RegistrationSlotPreference(
            registration_id=obj.id,
            offering_slot_id=slot.id,
            priority=priority
        )
        db.session.add(pref_obj)

    db.session.flush()
    return obj


def seed():
    print("🌱 Seeding started")

    for item in load_json("course_categories.json"):
        get_or_create_category(item)

    for item in load_json("teachers.json"):
        get_or_create_teacher(item)

    for item in load_json("assistants.json"):
        get_or_create_assistant(item)

    for item in load_json("classrooms.json"):
        get_or_create_classroom(item)

    for item in load_json("courses.json"):
        get_or_create_course(item)

    for item in load_json("students.json"):
        get_or_create_student(item)

    for item in load_json("parents.json"):
        get_or_create_parent(item)

    for item in load_json("student_registrations.json"):
        get_or_create_student_registration(item)

    for item in load_json("teacher_offering_slots.json"):
        get_or_create_teacher_offering_slot(item)

    for item in load_json("course_registrations.json"):
        get_or_create_course_registration(item)

    db.session.commit()
    print("✅ Demo data seeded successfully")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed()
