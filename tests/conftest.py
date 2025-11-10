import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import create_app, db as _db

@pytest.fixture(scope='function')
def app():
    """Создает приложение - БЕЗ автоочистки!"""
    class TestConfig:
        TESTING = True
        DEBUG = True
        SECRET_KEY = 'test-secret-key'
        JWT_SECRET_KEY = 'test-jwt-key'
        SQLALCHEMY_DATABASE_URI = 'postgresql://admin:password@localhost:5432/schedule_system'
        SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    app = create_app(TestConfig())
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db_session(app):
    """Просто возвращает сессию БД - ЧИСТИМ ВРУЧНУЮ!"""
    with app.app_context():
        yield _db.session
@pytest.fixture
def test_data(app):
    """Добавляет тестовые данные и КОММИТИТ их!"""
    with app.app_context():
        from tests.test_utils import create_test_data, cleanup_test_data
        from src.app import db
        
        # Очищаем и создаем заново
        cleanup_test_data(db.session)
        teacher, category, course, schedule = create_test_data(db.session)
        
        # КОММИТИМ!
        db.session.commit()
        
        print(f"✅ Тестовые данные созданы:")
        print(f"   Преподаватель: {teacher.lastname} {teacher.firstname}")
        print(f"   Курс: {course.name}")
        print(f"   Расписание: {schedule.day_of_week} день")
        
        yield
        
        # Чистим после теста
        cleanup_test_data(db.session)
        db.session.commit()