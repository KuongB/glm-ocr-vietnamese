"""
Health Check Routes
"""

from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.config import settings

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version=settings.VERSION
    )

@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "OCR Service API",
        "version": settings.VERSION,
        "docs": "/api/docs"
    }
