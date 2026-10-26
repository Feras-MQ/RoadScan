from roadscan.easy_start import prepare
from roadscan.accounts import authenticate


def test_first_run_creates_admin_and_preserves_on_restart(tmp_path, monkeypatch):
    monkeypatch.delenv("ROADSCAN_ACCOUNTS_FILE", raising=False)
    monkeypatch.setenv("ROADSCAN_ACCOUNTS_FILE", str(tmp_path / "private_accounts.json"))
    copied = []
    token, path = prepare(tmp_path, clipboard=copied.append)
    assert copied == [token]
    assert authenticate(token, str(path)) == {'actor': 'supervisor', 'role': 'admin'}
    again, same_path = prepare(tmp_path)
    assert again is None and same_path == path
    assert authenticate(token, str(path))['role'] == 'admin'


def test_account_file_stores_only_token_hash(tmp_path, monkeypatch):
    monkeypatch.delenv("ROADSCAN_ACCOUNTS_FILE", raising=False)
    monkeypatch.setenv("ROADSCAN_ACCOUNTS_FILE", str(tmp_path / "private_accounts.json"))
    token, path = prepare(tmp_path)
    assert token not in path.read_text()
