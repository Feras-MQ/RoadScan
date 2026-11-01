import pytest
from roadscan.accounts import create_account_file, update_account_file, authenticate


def test_add_and_revoke(tmp_path):
    path = str(tmp_path / 'accounts.json')
    admin = create_account_file(path, 'admin', 'admin')
    reviewer = update_account_file(path, 'add', 'alice', 'reviewer')
    assert authenticate(admin, path)['role'] == 'admin'
    assert authenticate(reviewer, path)['actor'] == 'alice'
    with pytest.raises(ValueError):
        update_account_file(path, 'add', 'alice', 'reviewer')
    update_account_file(path, 'revoke', 'alice')
    assert authenticate(reviewer, path) is None
    with pytest.raises(ValueError):
        update_account_file(path, 'revoke', 'admin')


def test_account_updates_without_windows_fchmod(tmp_path, monkeypatch):
    import os
    from roadscan.accounts import rotate_account_token
    monkeypatch.delattr(os, 'fchmod', raising=False)
    path = str(tmp_path / 'windows-accounts.json')
    admin = create_account_file(path, 'admin', 'admin')
    reviewer = update_account_file(path, 'add', 'alice', 'reviewer')
    assert authenticate(admin, path)['role'] == 'admin'
    assert authenticate(reviewer, path)['actor'] == 'alice'

    replacement = rotate_account_token(path, 'alice')
    assert authenticate(reviewer, path) is None
    assert authenticate(replacement, path)['actor'] == 'alice'
