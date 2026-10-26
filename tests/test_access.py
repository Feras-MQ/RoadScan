import os
from fastapi.testclient import TestClient
from roadscan.api import app


def test_roles(monkeypatch):
    monkeypatch.setenv('ROADSCAN_REVIEWER_KEY', 'reviewer-test-secret')
    monkeypatch.setenv('ROADSCAN_VIEWER_KEY', 'viewer-test-secret')
    with TestClient(app) as client:
        viewer = {'X-API-Key': 'viewer-test-secret'}
        reviewer = {'X-API-Key': 'reviewer-test-secret'}
        assert client.get('/api/reports', headers=viewer).status_code == 200
        assert client.get('/api/reports', headers=reviewer).status_code == 200
        assert client.post('/api/reports', headers=viewer).status_code == 403
        assert client.delete('/api/reports/unknown', headers=reviewer).status_code == 403
        assert client.get('/api/reports', headers={'X-API-Key': 'wrong'}).status_code == 401
