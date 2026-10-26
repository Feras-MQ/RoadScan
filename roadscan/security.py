"""Local API response hardening; not a replacement for deployment security."""
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Permissions-Policy'] = 'camera=(self), microphone=(), geolocation=()'
        if request.url.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
            response.headers['Pragma'] = 'no-cache'
        return response
