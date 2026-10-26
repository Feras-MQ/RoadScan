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
