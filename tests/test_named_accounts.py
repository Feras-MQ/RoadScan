import pytest
from fastapi.testclient import TestClient
from roadscan.accounts import create_account_file, authenticate
from roadscan.api import app


def test_named_accounts(tmp_path, monkeypatch):
    path = tmp_path / 'accounts.json'
    token = create_account_file(str(path), 'alice', 'reviewer')
    assert token not in path.read_text()
    assert authenticate(token, str(path)) == {'actor': 'alice', 'role': 'reviewer'}
    assert authenticate('incorrect', str(path)) is None
    with pytest.raises(FileExistsError):
        create_account_file(str(path), 'bob', 'admin')
    monkeypatch.setenv('ROADSCAN_ACCOUNTS_FILE', str(path))
    with TestClient(app) as client:
        assert client.get('/api/reports', headers={'X-API-Key': token}).status_code == 200
        assert client.delete('/api/reports/missing', headers={'X-API-Key': token}).status_code == 403
        assert client.get('/api/reports', headers={'X-API-Key': 'wrong'}).status_code == 401


def test_invalid_accounts_fail_closed(tmp_path, monkeypatch):
    path = tmp_path / 'bad.json'
    path.write_text('not json')
    monkeypatch.setenv('ROADSCAN_ACCOUNTS_FILE', str(path))
    with TestClient(app) as client:
        assert client.get('/api/reports', headers={'X-API-Key': 'anything'}).status_code == 503
