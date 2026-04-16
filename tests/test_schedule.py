def test_api_root(client):
    response = client.get('/api/')
    assert response.status_code == 200
    payload = response.get_json()
    assert payload == {
        'service': 'schedule-system',
        'status': 'ok',
        'api_prefix': '/api',
    }


def test_health_endpoint(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok'}


def test_unknown_route_returns_404(client):
    response = client.get('/api/does-not-exist')
    assert response.status_code == 404
