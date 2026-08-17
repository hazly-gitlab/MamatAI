import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from collections import defaultdict
from app.core.config import settings

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "connect-src 'self' ws: wss: http: https:; "
            "img-src 'self' data: blob: https:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "media-src 'self' blob: data:;"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/health", "/readiness", "/liveness"] or "ws" in request.url.path:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < 60]

        if len(self.requests[client_ip]) >= settings.RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."}
            )

        self.requests[client_ip].append(now)
        return await call_next(request)
