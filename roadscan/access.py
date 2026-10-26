"""Local key-based role separation. Pilot deployment requires real identity provider."""
import hmac
import os
from fastapi import Header, HTTPException


def identity(x_api_key: str | None = Header(default=None)) -> dict:
    account_file = os.getenv('ROADSCAN_ACCOUNTS_FILE')
    if account_file:
        from .accounts import authenticate
        if not x_api_key:
            raise HTTPException(401, 'API key required')
        try:
            who = authenticate(x_api_key, account_file)
        except RuntimeError as exc:
            raise HTTPException(503, str(exc)) from exc
        if who is None:
            raise HTTPException(401, 'Invalid API key')
        return who
    keys = (
        ('admin', 'ROADSCAN_API_KEY', 'admin'),
        ('reviewer', 'ROADSCAN_REVIEWER_KEY', 'reviewer'),
        ('viewer', 'ROADSCAN_VIEWER_KEY', 'viewer'),
    )
    configured = [(name, os.getenv(env, ''), role) for name, env, role in keys]
    configured = [(name, key, role) for name, key, role in configured if key and key != 'replace-with-long-random-secret']
    if len({key for _, key, _ in configured}) != len(configured):
        raise HTTPException(503, 'API keys must be unique across roles')
    if not configured:
        raise HTTPException(503, 'Configure ROADSCAN_API_KEY or role-specific keys')
    if not x_api_key:
        raise HTTPException(401, 'API key required')
    for name, key, role in configured:
        if hmac.compare_digest(x_api_key, key):
            return {'actor': name, 'role': role}
    raise HTTPException(401, 'Invalid API key')


def require(*allowed):
    def dependency(x_api_key: str | None = Header(default=None)):
        who = identity(x_api_key)
        if who['role'] not in allowed:
            raise HTTPException(403, 'Insufficient role')
        return who['actor']
    return dependency

read_access = require('viewer', 'reviewer', 'admin')
review_access = require('reviewer', 'admin')
admin_access = require('admin')
