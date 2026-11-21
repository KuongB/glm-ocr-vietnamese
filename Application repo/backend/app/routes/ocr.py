"""
OCR API Routes
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
import base64
from app.models.schemas import OCRRequest, OCRResponse, ErrorResponse
from app.services.ocr_service import ocr_service

router = APIRouter()

@router.post("/extract", response_model=OCRResponse)
async def extract_text(request: OCRRequest):
    """
    Extract text from base64 encoded image
    
    - **image_b64**: Base64 encoded image string
    - **language**: Target language (default: vi)
    """
    try:
        result = await ocr_service.extract_text(request.image_b64)
        return OCRResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

@router.post("/upload", response_model=OCRResponse)
async def upload_and_extract(file: UploadFile = File(...)):
    """
    Upload image file and extract text
    
    - **file**: Image file (jpg, png, jpeg)
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and encode image
        image_bytes = await file.read()
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Process
        result = await ocr_service.extract_text(image_b64)
        return OCRResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")

@router.get("/supported-languages")
async def get_supported_languages():
    """Get list of supported languages"""
    return {
        "languages": [
            {"code": "vi", "name": "Vietnamese"},
            {"code": "en", "name": "English"},
            {"code": "mix", "name": "Mixed (Vietnamese + English)"}
        ]
    }
