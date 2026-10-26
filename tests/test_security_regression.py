from fastapi.testclient import TestClient
from roadscan.api import app

def test_duplicate_role_keys_fail_closed(monkeypatch):
    monkeypatch.setenv('ROADSCAN_API_KEY', 'same-secret')
    monkeypatch.setenv('ROADSCAN_VIEWER_KEY', 'same-secret')
    with TestClient(app) as client:
        assert client.get('/api/reports', headers={'X-API-Key':'same-secret'}).status_code == 503

def test_nonfinite_coordinates_rejected(monkeypatch):
    monkeypatch.setenv('ROADSCAN_API_KEY', 'admin-test-secret')
    monkeypatch.delenv('ROADSCAN_VIEWER_KEY', raising=False)
    with TestClient(app) as client:
        response=client.post('/api/reports',headers={'X-API-Key':'admin-test-secret'},data={'latitude':'NaN','longitude':'20'},files={'photo':('x.jpg',b'invalid','image/jpeg')})
        assert response.status_code == 422
