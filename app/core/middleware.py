"""
API Authentication Middleware
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from config.settings import settings
from app.core.logger import logger

class APIKeyMiddleware(BaseHTTPMiddleware):
    PUBLIC_PATHS = ["/health", "/docs", "/redoc", "/openapi.json"]

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)
        if not settings.API_KEY_ENABLED:
            return await call_next(request)
        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")
        if not api_key:
            raise HTTPException(status_code=401, detail="API key required")
        if api_key.startswith("Bearer "):
            api_key = api_key[7:]
        if settings.API_KEY and api_key != settings.API_KEY:
            raise HTTPException(status_code=403, detail="Invalid API key")
        return await call_next(request)