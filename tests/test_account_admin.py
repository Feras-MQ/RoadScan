import os
import pytest
from roadscan.accounts import create_account_file, update_account_file, rotate_account_token, authenticate
from roadscan.account_admin import main


def test_rotate_invalidates_old_token(tmp_path):
    path = str(tmp_path / 'accounts.json')
    old = create_account_file(path, 'root', 'admin')
    reviewer = update_account_file(path, 'add', 'sara', 'reviewer')
    new = rotate_account_token(path, 'sara')
    assert new != reviewer
    assert authenticate(reviewer, path) is None
    assert authenticate(new, path) == {'actor': 'sara', 'role': 'reviewer'}
    assert authenticate(old, path)['role'] == 'admin'


@pytest.mark.skipif(os.name == 'nt', reason='POSIX mode bits do not verify Windows ACLs')
def test_rotated_account_file_has_private_posix_permissions(tmp_path):
    path = str(tmp_path / 'accounts.json')
    create_account_file(path, 'root', 'admin')
    rotate_account_token(path, 'root')
    assert (tmp_path / 'accounts.json').stat().st_mode & 0o077 == 0


def test_rotate_missing_does_not_change_file(tmp_path):
    path = str(tmp_path / 'accounts.json')
    create_account_file(path, 'root', 'admin')
    original = (tmp_path / 'accounts.json').read_bytes()
    with pytest.raises(ValueError):
        rotate_account_token(path, 'unknown')
    assert (tmp_path / 'accounts.json').read_bytes() == original


def test_admin_cli_init_add_revoke(tmp_path, capsys):
    path = str(tmp_path / 'accounts.json')
    main(['--file', path, 'init', '--username', 'root'])
    main(['--file', path, 'add', '--username', 'viewer1', '--role', 'viewer'])
    main(['--file', path, 'revoke', '--username', 'viewer1'])
    assert 'Account revoked' in capsys.readouterr().out
