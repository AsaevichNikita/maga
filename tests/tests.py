import pytest
from src.app import create_app, db
from app.models import Teacher, Course, CourseCategory, Student, ScheduleSlot

@pytest.fixture
def client():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()

def test_schedule_crud(client):
    # Создать категорию
    client.post('/course_categories', json={'name':'Музыка'})
    # Создать преподавателя
    client.post('/teachers', json={'firstname':'Иван','lastname':'Петров','email':'ivan.petrov@example.com'})
    # Создать курс
    client.post('/courses', json={'name':'Гитара','teacher_id':1,'category_id':1})
    # Создать слот
    r = client.post('/schedule', json={'course_id':1,'day_of_week':1,'start_time':'18:00','end_time':'19:30','classroom':'4-101'})
    assert r.status_code == 201
    # Получить слот
    r2 = client.get('/schedule/1')
    assert r2.status_code == 200
    # Обновить слот
    r3 = client.put('/schedule/1', json={'start_time':'18:30','end_time':'20:00'})
    assert r3.status_code == 200
    # Удалить слот
    r4 = client.delete('/schedule/1')
    assert r4.status_code == 200
