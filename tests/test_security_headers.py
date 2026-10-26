from fastapi.testclient import TestClient
from roadscan.api import app


def test_sensitive_api_responses_are_not_cacheable():
    with TestClient(app) as client:
        response = client.get('/api/health')
        assert response.status_code == 200
        assert response.headers['cache-control'] == 'no-store'
        assert response.headers['x-content-type-options'] == 'nosniff'
        assert response.headers['x-frame-options'] == 'DENY'
        assert response.headers['referrer-policy'] == 'no-referrer'
        assert response.headers['permissions-policy'] == 'camera=(self), microphone=(), geolocation=()'


def test_unauthorized_responses_are_not_cacheable():
    with TestClient(app) as client:
        response = client.get('/api/reports', headers={'X-API-Key': 'wrong'})
        assert response.status_code == 401
        assert response.headers['cache-control'] == 'no-store'
