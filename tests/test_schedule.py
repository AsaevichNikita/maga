# tests/test_schedule.py
import pytest
from src.app import create_app, db

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()

def test_get_slots(client):
    resp = client.get('/schedule/')
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) >= 1

def test_create_slot(client):
    resp = client.post('/schedule/', json={
        'course_id': 1,
        'day_of_week': 3,
        'start_time': '17:00',
        'end_time': '18:30',
        'classroom': '4-104'
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['course_id'] == 1

def test_update_slot(client):
    client.post('/schedule/', json={
        'course_id': 1,
        'day_of_week': 3,
        'start_time': '17:00',
        'end_time': '18:30',
        'classroom': '4-104'
    })
    resp = client.put('/schedule/1', json={
        'start_time': '18:00',
        'end_time': '19:30'
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['start_time'] == '18:00'

def test_delete_slot(client):
    client.post('/schedule/', json={
        'course_id': 1,
        'day_of_week': 3,
        'start_time': '17:00',
        'end_time': '18:30',
        'classroom': '4-104'
    })
    resp = client.delete('/schedule/1')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['message'] == 'Deleted successfully'
