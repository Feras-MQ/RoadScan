"""Optional local named access tokens. Not a production identity provider."""
import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path

ROLES = {'admin', 'reviewer', 'viewer'}


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def create_account_file(path: str, username: str, role: str) -> str:
    if not username or len(username) > 80 or not all(c.isalnum() or c in '._-' for c in username):
        raise ValueError('Username must be 1-80 letters, digits, dots, underscores or hyphens')
    if role not in ROLES:
        raise ValueError('Invalid role')
    target = Path(path)
    if target.exists():
        raise FileExistsError('Account file exists; refusing to overwrite existing accounts')
    token = secrets.token_urlsafe(32)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x', encoding='utf-8') as handle:
        os.chmod(target, 0o600)
        json.dump({'accounts': [{'username': username, 'role': role, 'token_sha256': token_digest(token)}]}, handle, indent=2)
    return token


def authenticate(token: str, path: str) -> dict | None:
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise RuntimeError('Named accounts file is unreadable or invalid') from exc
    accounts = data.get('accounts')
    if not isinstance(accounts, list):
        raise RuntimeError('Named accounts format is invalid')
    digest = token_digest(token)
    found = None
    for account in accounts:
        if not isinstance(account, dict) or account.get('role') not in ROLES or not isinstance(account.get('username'), str) or not isinstance(account.get('token_sha256'), str):
            raise RuntimeError('Named account record is invalid')
        if hmac.compare_digest(digest, account['token_sha256']):
            found = {'actor': account['username'], 'role': account['role']}
    return found


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Create first named local RoadScan account; token shown once')
    parser.add_argument('--file', required=True)
    parser.add_argument('--username', required=True)
    parser.add_argument('--role', choices=sorted(ROLES), required=True)
    args = parser.parse_args()
    print('Token (save securely; shown once):', create_account_file(args.file, args.username, args.role))


def update_account_file(path: str, action: str, username: str, role: str | None = None) -> str | None:
    """Add or revoke a local token, atomically replacing the account file.

    Existing tokens remain valid on add. Revoked tokens fail on next request.
    """
    import tempfile
    target = Path(path)
    if not target.is_file():
        raise FileNotFoundError('Create the initial account first')
    if not username or len(username) > 80 or not all(c.isalnum() or c in '._-' for c in username):
        raise ValueError('Invalid username')
    data = json.loads(target.read_text(encoding='utf-8'))
    accounts = data.get('accounts')
    if not isinstance(accounts, list) or any(not isinstance(a, dict) or a.get('role') not in ROLES or not isinstance(a.get('username'), str) or not isinstance(a.get('token_sha256'), str) for a in accounts):
        raise ValueError('Invalid account file')
    if len({a['username'] for a in accounts}) != len(accounts):
        raise ValueError('Duplicate usernames')
    existing = [a for a in accounts if a['username'] == username]
    token = None
    if action == 'add':
        if role not in ROLES or existing:
            raise ValueError('Role invalid or username already exists')
        token = secrets.token_urlsafe(32)
        accounts.append({'username': username, 'role': role, 'token_sha256': token_digest(token)})
    elif action == 'revoke':
        if not existing:
            raise ValueError('Username not found')
        if existing[0]['role'] == 'admin' and sum(a['role'] == 'admin' for a in accounts) <= 1:
            raise ValueError('Cannot revoke the last administrator')
        accounts = [a for a in accounts if a['username'] != username]
    else:
        raise ValueError('Unsupported action')
    fd, tmp = tempfile.mkstemp(prefix='.roadscan-accounts-', dir=target.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump({'accounts': accounts}, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return token


def rotate_account_token(path: str, username: str) -> str:
    """Atomically replace an existing token, invalidating the previous token immediately."""
    import tempfile
    target = Path(path)
    data = json.loads(target.read_text(encoding='utf-8'))
    accounts = data.get('accounts')
    if not isinstance(accounts, list) or any(
        not isinstance(a, dict) or a.get('role') not in ROLES
        or not isinstance(a.get('username'), str)
        or not isinstance(a.get('token_sha256'), str)
        for a in accounts
    ):
        raise ValueError('Invalid account file')
    matches = [a for a in accounts if a['username'] == username]
    if len(matches) != 1:
        raise ValueError('Account must exist exactly once')
    token = secrets.token_urlsafe(32)
    matches[0]['token_sha256'] = token_digest(token)
    fd, temp = tempfile.mkstemp(prefix='.roadscan-accounts-', dir=target.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(data, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, target)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return token
