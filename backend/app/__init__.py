"""
OCR Backend Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title=settings.APP_NAME,
        description="Professional OCR Service API",
        version=settings.VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routes
    from app.routes import ocr, health
    app.include_router(health.router, prefix="/api", tags=["Health"])
    app.include_router(ocr.router, prefix="/api/ocr", tags=["OCR"])
    
    return app
