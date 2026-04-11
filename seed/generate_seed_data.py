import json
import random
from pathlib import Path
from datetime import date, timedelta

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

# Мягко добавляем нужный год, но не размазываем всё совсем равномерно
ACADEMIC_YEARS = ["2025/2026", "2026/2027", "2027/2028"]
ACADEMIC_YEAR_WEIGHTS = {
    "2025/2026": 0.60,
    "2026/2027": 0.25,
    "2027/2028": 0.15,
}

TEACHERS_COUNT = 24
ASSISTANTS_COUNT = 10
STUDENTS_COUNT = 400
PARENTS_COUNT = 300
COURSES_PER_CATEGORY = 4


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


def weighted_year_choice(available_years):
    years = [y for y in ACADEMIC_YEARS if y in available_years]
    if not years:
        return None
    weights = [ACADEMIC_YEAR_WEIGHTS[y] for y in years]
    total = sum(weights)
    norm = [w / total for w in weights]
    return random.choices(years, weights=norm, k=1)[0]


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
    for idx, name in enumerate(CLASSROOM_NAMES, start=1):
        result.append({
            "name": name,
            "capacity": random.choice([10, 12, 15, 18, 20])
        })
    return result


def make_categories():
    result = []
    for idx, (name, description) in enumerate(CATEGORY_NAMES, start=1):
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
            # Чуть уже пул преподавателей на курс, чтобы не дробить спрос слишком сильно
            allowed = random.sample(teacher_emails, k=random.randint(2, 4))
            result.append({
                "name": course_name,
                "description": f"{course_name} — расширенная программа",
                "category_name": category_name,
                "max_students": random.choice([10, 12, 15, 18]),
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

    def try_create_slot(course, teacher_email, academic_year, day, start_time, end_time):
        teacher_key = (academic_year, teacher_email, day, start_time, end_time)
        if teacher_key in teacher_busy:
            return None

        shuffled_rooms = classroom_names[:]
        random.shuffle(shuffled_rooms)
        chosen_room = None

        for room_name in shuffled_rooms:
            room_key = (academic_year, room_name, day, start_time, end_time)
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
            "academic_year": academic_year,
            "day_of_week": day,
            "start_time": start_time,
            "end_time": end_time,
            "classroom_name": chosen_room,
            "is_active": True,
            "max_groups": 1,
            "priority": random.choice([50, 80, 100, 120])
        }

    for course in courses:
        teacher_emails = course["allowed_teacher_emails"]

        for academic_year in ACADEMIC_YEARS:
            if academic_year == "2025/2026":
                slot_count = random.randint(2, 3)
            else:
                slot_count = random.randint(1, 2)

            used_windows = set()

            for _ in range(slot_count):
                attempts = 0
                created = False

                while attempts < 30 and not created:
                    attempts += 1
                    teacher_email = random.choice(teacher_emails)
                    day = random.randint(1, 6)
                    start_time, end_time = random.choice(TIME_WINDOWS)
                    window_key = (day, start_time, end_time)

                    # иногда даём два преподавателя в одно окно, но умеренно
                    allow_parallel_same_window = random.random() < 0.25

                    if window_key in used_windows and not allow_parallel_same_window:
                        continue

                    item = try_create_slot(
                        course=course,
                        teacher_email=teacher_email,
                        academic_year=academic_year,
                        day=day,
                        start_time=start_time,
                        end_time=end_time
                    )
                    if item:
                        result.append(item)
                        used_windows.add(window_key)
                        created = True

    return result


def make_course_registrations(students, courses, offering_slots, max_per_student=3):
    slots_by_course_year = {}
    windows_by_course_year = {}
    years_by_course = {}

    for slot in offering_slots:
        key = (slot["course_name"], slot["academic_year"])
        slots_by_course_year.setdefault(key, []).append(slot)
        years_by_course.setdefault(slot["course_name"], set()).add(slot["academic_year"])

        window_key = (
            slot["day_of_week"],
            slot["start_time"],
            slot["end_time"]
        )
        windows_by_course_year.setdefault(key, {}).setdefault(window_key, []).append(slot)

    result = []
    used = set()

    for st in students:
        regs_count = random.choices([1, 2, 3], weights=[0.20, 0.45, 0.35], k=1)[0]
        selected_courses = random.sample(courses, k=min(regs_count, len(courses)))

        for course in selected_courses:
            key = (st["email"], course["name"])
            if key in used:
                continue

            available_years = sorted(years_by_course.get(course["name"], []))
            academic_year = weighted_year_choice(available_years)
            if not academic_year:
                continue

            possible_windows = windows_by_course_year.get((course["name"], academic_year), {})
            if not possible_windows:
                continue

            used.add(key)

            # Мягкий баланс rigid/flex
            scenario = random.choices(
                ["rigid_single", "rigid_same_window_multi", "flex_2", "flex_3"],
                weights=[0.18, 0.17, 0.40, 0.25],
                k=1
            )[0]

            slot_preferences = []

            if scenario == "rigid_single":
                chosen_window = random.choice(list(possible_windows.keys()))
                slot = random.choice(possible_windows[chosen_window])
                slot_preferences.append(slot)

            elif scenario == "rigid_same_window_multi":
                candidate_windows = [w for w, items in possible_windows.items() if len(items) >= 2]
                if candidate_windows:
                    chosen_window = random.choice(candidate_windows)
                    items = possible_windows[chosen_window][:]
                    random.shuffle(items)
                    slot_preferences.extend(items[:2])
                else:
                    chosen_window = random.choice(list(possible_windows.keys()))
                    slot = random.choice(possible_windows[chosen_window])
                    slot_preferences.append(slot)

            elif scenario == "flex_2":
                chosen_windows = random.sample(
                    list(possible_windows.keys()),
                    k=min(2, len(possible_windows))
                )
                for w in chosen_windows:
                    slot_preferences.append(random.choice(possible_windows[w]))

            else:  # flex_3
                chosen_windows = random.sample(
                    list(possible_windows.keys()),
                    k=min(3, len(possible_windows))
                )
                for w in chosen_windows:
                    slot_preferences.append(random.choice(possible_windows[w]))

            # дедуп по фактическому слоту
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
                "academic_year": academic_year,
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
    print(f"Учебные годы: {', '.join(ACADEMIC_YEARS)}")
    print(f"Преподавателей: {len(teachers)}")
    print(f"Студентов: {len(students)}")
    print(f"Offering slots: {len(offering_slots)}")
    print(f"Course registrations: {len(course_regs)}")


if __name__ == "__main__":
    main()