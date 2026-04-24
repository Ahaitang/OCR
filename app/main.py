"""
FastAPI application entry point - OCR Service only
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.api.router_ocr import router as ocr_router


def create_app() -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(
        title="Hospital OCR Service",
        version="1.0.0",
        description="医疗记录 OCR 解析服务 - PaddleOCR",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"]
    )

    # Health check endpoint
    @app.get("/health", tags=["System"])
    def health_check():
        """Service health check"""
        return {
            "code": 200,
            "message": "healthy",
            "data": {
                "service": "hospital-ocr",
                "version": "1.0.0",
                "timestamp": datetime.now().isoformat()
            }
        }

    # Register OCR router
    app.include_router(ocr_router, prefix="/api/ocr", tags=["OCR"])

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )