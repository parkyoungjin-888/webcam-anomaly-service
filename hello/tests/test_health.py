from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_returns_ok():
    res = client.get('/health')
    assert res.status_code == 200
    assert res.json()['status'] == 'ok'


def test_root_reports_app_name():
    res = client.get('/')
    assert res.status_code == 200
    assert 'app' in res.json()
