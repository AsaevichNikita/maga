from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flasgger import Swagger

# Создаем экземпляры расширений
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app(config_object=None):
    """
    Функция фабрики приложения Flask
    """
    app = Flask(__name__)
    Swagger(app)
    # Загружаем базовую конфигурацию
    from src.config import Config
    app.config.from_object(Config)
    
    # Загружаем кастомную конфигурацию, если передана
    if config_object is not None:
        app.config.from_object(config_object)
    
    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Импортируем модели после инициализации db
    from app import models  # noqa: F401
    
    # Регистрируем Blueprints
    from app.routes.main import main_bp
    from app.routes.schedule import schedule_bp
    from app.routes.registration import registration_bp
    from app.routes.students import students_bp
    from app.routes.courses import courses_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(schedule_bp, url_prefix='/schedule')
    app.register_blueprint(registration_bp, url_prefix='/registration')
    app.register_blueprint(students_bp, url_prefix='/students')
    app.register_blueprint(courses_bp, url_prefix='/courses')
    
    return app
