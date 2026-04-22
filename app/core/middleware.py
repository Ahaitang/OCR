"""
API Authentication Middleware
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.logger import logger


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to validate API key for protected endpoints"""

    # Public endpoints that don't require authentication
    PUBLIC_PATHS = [
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json"
    ]

    async def dispatch(self, request: Request, call_next):
        # Skip authentication for public paths
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        # Skip if API key authentication is disabled
        if not settings.API_KEY_ENABLED:
            return await call_next(request)

        # Check for API key in header
        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")

        if not api_key:
            logger.warning(f"Missing API key for {request.url.path}")
            raise HTTPException(
                status_code=401,
                detail="API key required. Provide X-API-Key header."
            )

        # Remove 'Bearer ' prefix if present
        if api_key.startswith("Bearer "):
            api_key = api_key[7:]

        # Validate API key
        if settings.API_KEY and api_key != settings.API_KEY:
            logger.warning(f"Invalid API key attempt for {request.url.path}")
            raise HTTPException(
                status_code=403,
                detail="Invalid API key"
            )

        return await call_next(request)