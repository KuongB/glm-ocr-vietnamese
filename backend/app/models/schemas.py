"""
Pydantic schemas for OCR API
"""

from pydantic import BaseModel
from typing import Optional


class OCRRequest(BaseModel):
    """Request schema for OCR extraction"""
    image_b64: str


class OCRResponse(BaseModel):
    """Response schema for OCR extraction"""
    text: str
    processing_time: float
    confidence: Optional[float] = None


class ErrorResponse(BaseModel):
    """Error response schema"""
    detail: str
    status_code: int = 500


class HealthResponse(BaseModel):
    """Health check response schema"""
    status: str
    version: str
