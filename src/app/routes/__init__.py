from __future__ import annotations

from flask import Flask

from .assistant_substitutions import assistant_substitutions_bp
from .assistants import assistants_bp
from .auth import auth_bp
from .classrooms import classrooms_bp
from .course_categories import course_categories_bp
from .course_groups import course_groups_bp
from .courses import courses_bp
from .informatics_blocks import informatics_blocks_bp
from .main import main_bp
from .registration import registration_bp
from .schedule import schedule_bp
from .schedule_generation import schedule_generation_bp
from .search import search_bp
from .students import students_bp
from .teacher_offering_slots import teacher_offering_slots_bp
from .teachers import teachers_bp


BLUEPRINTS = (
    (main_bp, ""),
    (schedule_bp, "/schedule"),
    (registration_bp, "/registration"),
    (students_bp, "/students"),
    (courses_bp, "/courses"),
    (teachers_bp, "/teachers"),
    (assistants_bp, "/assistants"),
    (course_categories_bp, "/course-categories"),
    (course_groups_bp, "/course-groups"),
    (classrooms_bp, "/classrooms"),
    (assistant_substitutions_bp, "/assistant-substitutions"),
    (teacher_offering_slots_bp, "/teacher-offering-slots"),
    (auth_bp, "/auth"),
    (schedule_generation_bp, "/schedule-generation"),
    (informatics_blocks_bp, "/informatics-blocks"),
    (search_bp, "/search"),
)


def register_blueprints(app: Flask, api_prefix: str = "/api") -> None:
    for blueprint, suffix in BLUEPRINTS:
        app.register_blueprint(blueprint, url_prefix=f"{api_prefix}{suffix}")
