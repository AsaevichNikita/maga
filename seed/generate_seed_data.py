import json
import random
from pathlib import Path
from datetime import date, timedelta, datetime

random.seed(42)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FIRST_NAMES_M = [
    "Иван", "Пётр", "Алексей", "Сергей", "Дмитрий", "Андрей", "Максим",
    "Никита", "Егор", "Михаил", "Артём", "Владимир", "Павел", "Константин"
]
FIRST_NAMES_F = [
    "Анна", "Мария", "Ольга", "Елена", "Ирина", "Наталья", "Светлана",
    "Татьяна", "Юлия", "Екатерина", "Виктория", "Алиса", "Дарья", "Полина"
]
LAST_NAMES_M = [
    "Иванов", "Петров", "Сидоров", "Кузнецов", "Смирнов", "Орлов",
    "Васильев", "Фёдоров", "Морозов", "Волков", "Соколов", "Зайцев"
]
LAST_NAMES_F = [
    "Иванова", "Петрова", "Сидорова", "Кузнецова", "Смирнова", "Орлова",
    "Васильева", "Фёдорова", "Морозова", "Волкова", "Соколова", "Зайцева"
]
PATRONYMICS_M = [
    "Иванович", "Петрович", "Сергеевич", "Алексеевич", "Дмитриевич",
    "Андреевич", "Павлович", "Максимович"
]
PATRONYMICS_F = [
    "Ивановна", "Петровна", "Сергеевна", "Алексеевна", "Дмитриевна",
    "Андреевна", "Павловна", "Максимовна"
]

CATEGORY_NAMES = [
    ("Программирование", "Курсы по программированию"),
    ("Математика", "Курсы по математике"),
    ("Робототехника", "Курсы по робототехнике"),
    ("Дизайн", "Курсы по дизайну"),
    ("Английский язык", "Курсы по английскому языку"),
    ("Шахматы", "Курсы по шахматам"),
    ("Физика", "Курсы по физике"),
    ("Подготовка к олимпиадам", "Олимпиадные курсы")
]

COURSE_POOL = {
    "Программирование": [
        "Python для начинающих", "Python Pro", "Web-разработка", "Алгоритмы и структуры данных"
    ],
    "Математика": [
        "Олимпиадная математика", "Логика и задачи", "Алгебра+", "Геометрия без страха"
    ],
    "Робототехника": [
        "Роботы LEGO", "Основы Arduino", "Робототехника Start", "Умные устройства"
    ],
    "Дизайн": [
        "Графический дизайн", "UI/UX основы", "Цифровая иллюстрация", "3D-моделирование"
    ],
    "Английский язык": [
        "English Start", "Spoken English", "Grammar Boost", "English for Teens"
    ],
    "Шахматы": [
        "Шахматы Start", "Тактика в шахматах", "Шахматный клуб", "Турнирная подготовка"
    ],
    "Физика": [
        "Физика Start", "Практическая физика", "Эксперименты и наука", "Физика для олимпиад"
    ],
    "Подготовка к олимпиадам": [
        "Олимпиадный трек", "Подготовка к перечневым", "Интенсив по задачам", "Сборная школы"
    ],
}

CLASSROOM_NAMES = [
    "Кабинет 101", "Кабинет 102", "Кабинет 103", "Кабинет 104",
    "Кабинет 201", "Кабинет 202", "Кабинет 203",
    "Компьютерный класс 1", "Компьютерный класс 2", "Лаборатория",
    "Медиа-класс", "Коворкинг", "Аудитория А", "Аудитория Б"
]

TIME_WINDOWS = [
    ("14:00", "15:30"),
    ("15:40", "17:10"),
    ("17:20", "18:50"),
    ("10:00", "11:30"),
    ("11:40", "13:10"),
]

TEACHERS_COUNT = 28
ASSISTANTS_COUNT = 12
STUDENTS_COUNT = 420
PARENTS_COUNT = 320
COURSES_PER_CATEGORY = 4


def current_academic_year():
    year = datetime.now().year
    return f"{year}-{year + 1}"


ACADEMIC_YEAR = current_academic_year()


def dump(name, data):
    path = DATA_DIR / name
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ {path} ({len(data)} records)")


def random_phone(offset):
    return f"+7999{offset:07d}"


def random_birthdate(year_from, year_to):
    start = date(year_from, 1, 1)
    end = date(year_to, 12, 31)
    delta = (end - start).days
    return (start + timedelta(days=random.randint(0, delta))).isoformat()


def make_teachers(n=TEACHERS_COUNT):
    result = []
    for i in range(1, n + 1):
        first = random.choice(FIRST_NAMES_M if i % 2 else FIRST_NAMES_F)
        last = random.choice(LAST_NAMES_M if i % 2 else LAST_NAMES_F)
        patr = random.choice(PATRONYMICS_M if i % 2 else PATRONYMICS_F)
        result.append({
            "firstname": first,
            "lastname": last,
            "surname": patr,
            "birthday": random_birthdate(1975, 1996),
            "phone_number": random_phone(1000000 + i),
            "email": f"teacher{i}@maga.local"
        })
    return result


def make_assistants(n=ASSISTANTS_COUNT):
    result = []
    for i in range(1, n + 1):
        first = random.choice(FIRST_NAMES_F if i % 2 else FIRST_NAMES_M)
        last = random.choice(LAST_NAMES_F if i % 2 else LAST_NAMES_M)
        patr = random.choice(PATRONYMICS_F if i % 2 else PATRONYMICS_M)
        result.append({
            "firstname": first,
            "lastname": last,
            "surname": patr,
            "birthday": random_birthdate(1998, 2005),
            "phone_number": random_phone(2000000 + i),
            "email": f"assistant{i}@maga.local"
        })
    return result


def make_classrooms():
    result = []
    capacities = [10, 12, 14, 16, 18, 20]
    for name in CLASSROOM_NAMES:
        result.append({
            "name": name,
            "capacity": random.choice(capacities)
        })
    return result


def make_categories():
    result = []
    for name, description in CATEGORY_NAMES:
        min_grade = random.choice([1, 3, 5, 7])
        max_grade = random.choice([9, 10, 11])
        if max_grade < min_grade:
            min_grade, max_grade = max_grade, min_grade

        result.append({
            "name": name,
            "description": description,
            "min_grade": min_grade,
            "max_grade": max_grade
        })
    return result


def make_courses(teachers, per_category=COURSES_PER_CATEGORY):
    teacher_emails = [x["email"] for x in teachers]
    result = []

    for category_name, _ in CATEGORY_NAMES:
        names = COURSE_POOL[category_name][:per_category]
        for course_name in names:
            allowed = random.sample(teacher_emails, k=random.randint(2, 4))
            result.append({
                "name": course_name,
                "description": f"{course_name} — расширенная программа",
                "category_name": category_name,
                "max_students": random.choice([10, 12, 14, 16]),
                "use_classroom_capacity": random.choice([True, False]),
                "duration_minutes": random.choice([60, 90]),
                "price": random.choice([2500, 3000, 3500, 4000]),
                "is_active": True,
                "allowed_teacher_emails": allowed
            })

    return result


def make_students(n=STUDENTS_COUNT):
    result = []
    for i in range(1, n + 1):
        first = random.choice(FIRST_NAMES_M if i % 2 else FIRST_NAMES_F)
        last = random.choice(LAST_NAMES_M if i % 2 else LAST_NAMES_F)
        patr = random.choice(PATRONYMICS_M if i % 2 else PATRONYMICS_F)
        grade = random.randint(1, 11)
        letter = random.choice(["А", "Б", "В"])

        result.append({
            "firstname": first,
            "lastname": last,
            "surname": patr,
            "phone_number": random_phone(3000000 + i),
            "email": f"student{i}@maga.local",
            "birthday": random_birthdate(2009, 2018),
            "address": f"ул. Учебная, д. {random.randint(1, 150)}",
            "educational_institution": f"Школа №{random.randint(1, 25)}",
            "group_name": f"{grade}{letter}",
            "education_type": "школьное",
            "enrolled_this_year": random.choice([True, False])
        })

    return result


def make_parents(n=PARENTS_COUNT):
    result = []
    for i in range(1, n + 1):
        first = random.choice(FIRST_NAMES_F if i % 2 else FIRST_NAMES_M)
        last = random.choice(LAST_NAMES_F if i % 2 else LAST_NAMES_M)
        patr = random.choice(PATRONYMICS_F if i % 2 else PATRONYMICS_M)

        result.append({
            "firstname": first,
            "lastname": last,
            "surname": patr,
            "birthday": random_birthdate(1972, 1990),
            "address": f"ул. Семейная, д. {random.randint(1, 150)}",
            "phone_number": random_phone(4000000 + i),
            "email": f"parent{i}@maga.local",
            "data_processing_consent": True
        })

    return result


def make_student_registrations(students, parents):
    result = []
    parent_emails = [x["email"] for x in parents]

    for st in students:
        result.append({
            "student_email": st["email"],
            "parent_email": random.choice(parent_emails)
        })

    return result


def make_teacher_offering_slots(courses, classrooms):
    classroom_names = [x["name"] for x in classrooms]
    result = []

    teacher_busy = set()
    classroom_busy = set()

    def try_create_slot(course, teacher_email, day, start_time, end_time):
        teacher_key = (ACADEMIC_YEAR, teacher_email, day, start_time, end_time)
        if teacher_key in teacher_busy:
            return None

        shuffled_rooms = classroom_names[:]
        random.shuffle(shuffled_rooms)
        chosen_room = None

        for room_name in shuffled_rooms:
            room_key = (ACADEMIC_YEAR, room_name, day, start_time, end_time)
            if room_key not in classroom_busy:
                chosen_room = room_name
                classroom_busy.add(room_key)
                break

        if chosen_room is None:
            return None

        teacher_busy.add(teacher_key)

        return {
            "teacher_email": teacher_email,
            "course_name": course["name"],
            "academic_year": ACADEMIC_YEAR,
            "day_of_week": day,
            "start_time": start_time,
            "end_time": end_time,
            "classroom_name": chosen_room,
            "is_active": True,
            "max_groups": 1,
            "priority": random.choice([60, 80, 100, 120])
        }

    for course in courses:
        teacher_emails = course["allowed_teacher_emails"]

        # Для каждого курса даём 3-4 устойчивых окна в текущем учебном году.
        slot_count = random.randint(3, 4)
        used_windows = set()
        created_for_course = 0
        attempts = 0

        while created_for_course < slot_count and attempts < 80:
            attempts += 1
            teacher_email = random.choice(teacher_emails)
            day = random.randint(1, 6)
            start_time, end_time = random.choice(TIME_WINDOWS)
            window_key = (day, start_time, end_time)

            if window_key in used_windows:
                continue

            item = try_create_slot(
                course=course,
                teacher_email=teacher_email,
                day=day,
                start_time=start_time,
                end_time=end_time
            )
            if item:
                result.append(item)
                used_windows.add(window_key)
                created_for_course += 1

        # Гарантируем хотя бы 2 слота на курс
        if created_for_course < 2:
            fallback_windows = TIME_WINDOWS[:]
            random.shuffle(fallback_windows)

            for start_time, end_time in fallback_windows:
                if created_for_course >= 2:
                    break
                for day in range(1, 7):
                    if created_for_course >= 2:
                        break
                    window_key = (day, start_time, end_time)
                    if window_key in used_windows:
                        continue

                    teacher_email = random.choice(teacher_emails)
                    item = try_create_slot(course, teacher_email, day, start_time, end_time)
                    if item:
                        result.append(item)
                        used_windows.add(window_key)
                        created_for_course += 1

    return result


def make_course_registrations(students, courses, offering_slots):
    slots_by_course = {}
    windows_by_course = {}

    for slot in offering_slots:
        course_name = slot["course_name"]
        slots_by_course.setdefault(course_name, []).append(slot)

        window_key = (
            slot["day_of_week"],
            slot["start_time"],
            slot["end_time"]
        )
        windows_by_course.setdefault(course_name, {}).setdefault(window_key, []).append(slot)

    result = []
    used = set()

    # Делаем спрос более плотным: 2-3 заявки на ученика.
    for st in students:
        regs_count = random.choices([2, 3], weights=[0.45, 0.55], k=1)[0]
        selected_courses = random.sample(courses, k=min(regs_count, len(courses)))

        for course in selected_courses:
            key = (st["email"], course["name"])
            if key in used:
                continue

            possible_windows = windows_by_course.get(course["name"], {})
            if not possible_windows:
                continue

            used.add(key)

            scenario = random.choices(
                ["rigid_single", "flex_2", "flex_3"],
                weights=[0.28, 0.42, 0.30],
                k=1
            )[0]

            slot_preferences = []

            if scenario == "rigid_single":
                chosen_window = random.choice(list(possible_windows.keys()))
                slot_preferences.append(random.choice(possible_windows[chosen_window]))

            elif scenario == "flex_2":
                chosen_windows = random.sample(
                    list(possible_windows.keys()),
                    k=min(2, len(possible_windows))
                )
                for w in chosen_windows:
                    slot_preferences.append(random.choice(possible_windows[w]))

            else:
                chosen_windows = random.sample(
                    list(possible_windows.keys()),
                    k=min(3, len(possible_windows))
                )
                for w in chosen_windows:
                    slot_preferences.append(random.choice(possible_windows[w]))

            deduped = []
            seen = set()
            for slot in slot_preferences:
                sig = (
                    slot["teacher_email"],
                    slot["course_name"],
                    slot["academic_year"],
                    slot["day_of_week"],
                    slot["start_time"],
                    slot["end_time"]
                )
                if sig in seen:
                    continue
                seen.add(sig)
                deduped.append(slot)

            prefs = []
            for idx, slot in enumerate(deduped, start=1):
                prefs.append({
                    "teacher_email": slot["teacher_email"],
                    "course_name": slot["course_name"],
                    "academic_year": slot["academic_year"],
                    "day_of_week": slot["day_of_week"],
                    "start_time": slot["start_time"],
                    "end_time": slot["end_time"],
                    "priority": idx
                })

            if not prefs:
                continue

            result.append({
                "student_email": st["email"],
                "course_name": course["name"],
                "academic_year": ACADEMIC_YEAR,
                "status": "pending",
                "level": random.randint(1, 10),
                "comment": random.choice([
                    "Интересуется направлением",
                    "Есть базовые знания",
                    "Хочет заниматься углубленно",
                    "Пробное направление",
                    None
                ]),
                "skills": random.sample(
                    ["логика", "алгоритмы", "математика", "конструирование", "рисование", "английский"],
                    k=random.randint(0, 3)
                ),
                "slot_preferences": prefs
            })

    return result


def main():
    teachers = make_teachers()
    assistants = make_assistants()
    classrooms = make_classrooms()
    categories = make_categories()
    courses = make_courses(teachers)
    students = make_students()
    parents = make_parents()
    student_regs = make_student_registrations(students, parents)
    offering_slots = make_teacher_offering_slots(courses, classrooms)
    course_regs = make_course_registrations(students, courses, offering_slots)

    dump("teachers.json", teachers)
    dump("assistants.json", assistants)
    dump("classrooms.json", classrooms)
    dump("course_categories.json", categories)
    dump("courses.json", courses)
    dump("students.json", students)
    dump("parents.json", parents)
    dump("student_registrations.json", student_regs)
    dump("teacher_offering_slots.json", offering_slots)
    dump("course_registrations.json", course_regs)

    print("🎉 Seed data generated successfully")
    print(f"Учебный год: {ACADEMIC_YEAR}")
    print(f"Преподавателей: {len(teachers)}")
    print(f"Студентов: {len(students)}")
    print(f"Offering slots: {len(offering_slots)}")
    print(f"Course registrations: {len(course_regs)}")


if __name__ == "__main__":
    main()