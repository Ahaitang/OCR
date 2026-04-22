"""
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import sys

sys.path.insert(0, ".")

from app.core.config import settings
from app.core.database import test_connection
from app.core.logger import logger
from app.core.scheduler import init_scheduler
from app.core.middleware import APIKeyMiddleware

# Import routers
from app.api.router_qmg import router as qmg_router
from app.api.router_neuro import router as neuro_router
from app.api.router_ocr import router as ocr_router


def create_app() -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(
        title=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
        description="Hospital AI Analysis Service - QMG Analysis, Neuroimmune Optimization, OCR",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # CORS middleware - restrict origins in production
    allowed_origins = settings.ALLOWED_ORIGINS if hasattr(settings, 'ALLOWED_ORIGINS') else [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080"
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key"]
    )

    # API Key authentication middleware
    app.add_middleware(APIKeyMiddleware)

    # Health check endpoint
    @app.get("/health", tags=["System"])
    def health_check():
        """Service health check"""
        db_ok = test_connection()
        return {
            "code": 200 if db_ok else 500,
            "message": "healthy" if db_ok else "database connection failed",
            "data": {
                "service": settings.SERVICE_NAME,
                "version": settings.SERVICE_VERSION,
                "timestamp": datetime.now().isoformat(),
                "database": "connected" if db_ok else "disconnected"
            }
        }

    # Register routers
    app.include_router(qmg_router, prefix="/api/qmg", tags=["QMG Analysis"])
    app.include_router(neuro_router, prefix="/api/neuro", tags=["Neuroimmune Optimization"])
    app.include_router(ocr_router, prefix="/api/ocr", tags=["OCR"])

    # Startup event
    @app.on_event("startup")
    async def startup_event():
        logger.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
        if test_connection():
            logger.info("Database connection established")
        else:
            logger.warning("Database connection failed - service may not work properly")

        # Initialize scheduler
        init_scheduler()

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )