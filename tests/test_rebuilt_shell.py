from pathlib import Path
from fastapi.testclient import TestClient
from roadscan.api import app

ROOT=Path(__file__).resolve().parent.parent

def test_react_source_and_packaging_present():
    for f in ('frontend/src/App.tsx','frontend/src/style.css','frontend/vite.config.ts','desktop/main.cjs','desktop/preload.cjs','compose.yaml','Dockerfile','START_DOCKER_WINDOWS.cmd'):
        assert (ROOT/f).is_file(), f

def test_react_or_legacy_ui_served():
    with TestClient(app) as client:
        result=client.get('/')
        assert result.status_code==200
        assert 'text/html' in result.headers['content-type']
        assert client.get('/api/health').status_code==200

def test_desktop_backend_requires_key(monkeypatch):
    from roadscan.desktop_server import main
    import pytest
    monkeypatch.delenv('ROADSCAN_API_KEY',raising=False)
    with pytest.raises(SystemExit,match='Missing desktop session token'):
        main()
