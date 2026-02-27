from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flasgger import Swagger
from prometheus_flask_exporter import PrometheusMetrics

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()


def create_app(config_object=None):
    app = Flask(__name__)
    Swagger(app)

    from src.config import Config
    app.config.from_object(Config)
    if config_object is not None:
        app.config.from_object(config_object)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    metrics = PrometheusMetrics(app)
    metrics.info('app_info', 'Schedule system', version='1.0.0')

    # важно: чтобы SQLAlchemy "увидел" модели
    from src.app import models  # noqa: F401

    # ✅ imports blueprints (ВАЖНО: через src.app / относительные)
    from .routes.main import main_bp
    from .routes.schedule import schedule_bp
    from .routes.registration import registration_bp
    from .routes.students import students_bp
    from .routes.courses import courses_bp
    from .routes.teachers import teachers_bp

    from .routes.assistants import assistants_bp
    from .routes.course_categories import course_categories_bp
    from .routes.course_groups import course_groups_bp
    from .routes.classrooms import classrooms_bp
    from .routes.assistant_substitutions import assistant_substitutions_bp

    API_PREFIX = "/api"

    app.register_blueprint(main_bp, url_prefix=API_PREFIX)
    app.register_blueprint(schedule_bp, url_prefix=f"{API_PREFIX}/schedule")
    app.register_blueprint(registration_bp, url_prefix=f"{API_PREFIX}/registration")

    app.register_blueprint(students_bp, url_prefix=f"{API_PREFIX}/students")
    app.register_blueprint(courses_bp, url_prefix=f"{API_PREFIX}/courses")
    app.register_blueprint(teachers_bp, url_prefix=f"{API_PREFIX}/teachers")

    app.register_blueprint(course_categories_bp, url_prefix=f"{API_PREFIX}/course-categories")
    app.register_blueprint(course_groups_bp, url_prefix=f"{API_PREFIX}/course-groups")
    app.register_blueprint(classrooms_bp, url_prefix=f"{API_PREFIX}/classrooms")
    app.register_blueprint(assistants_bp, url_prefix=f"{API_PREFIX}/assistants")
    app.register_blueprint(assistant_substitutions_bp, url_prefix=f"{API_PREFIX}/assistant-substitutions")
    from .routes.informatics_blocks import informatics_blocks_bp
    app.register_blueprint(informatics_blocks_bp, url_prefix=f"{API_PREFIX}/informatics-blocks")
    
    return app