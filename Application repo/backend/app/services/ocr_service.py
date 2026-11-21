"""
OCR Service - Business logic for OCR operations via Modal API
"""

import base64
import io
import time
import logging
import asyncio
from PIL import Image
from typing import Dict
import httpx
from app.config import settings

# Setup logging
logger = logging.getLogger(__name__)

class OCRService:
    """Service class for OCR operations using Modal API"""
    
    def __init__(self):
        self.modal_url = settings.MODAL_API_URL
    def validate_image(self, image_b64: str) -> bytes:
        """Validate and decode base64 image"""
        try:
            # Remove data URL prefix if present
            if ',' in image_b64:
                image_b64 = image_b64.split(',')[1]
            
            image_bytes = base64.b64decode(image_b64)
            
            # Validate image size
            if len(image_bytes) > settings.MAX_IMAGE_SIZE:
                raise ValueError(f"Image size exceeds maximum allowed size of {settings.MAX_IMAGE_SIZE} bytes")
            
            # Validate it's a valid image
            image = Image.open(io.BytesIO(image_bytes))
            image.verify()
            
            return image_bytes
        except Exception as e:
            raise ValueError(f"Invalid image data: {str(e)}")
    
    async def process_with_modal(self, image_bytes: bytes) -> str:
        """Process image using Modal API with retry logic"""
        if not self.modal_url:
            raise ValueError("MODAL_API_URL is not configured. Please set it in your .env file.")
        
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        max_retries = settings.MODAL_MAX_RETRIES
        timeout = settings.MODAL_TIMEOUT
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Calling Modal API (attempt {attempt + 1}/{max_retries})...")
                
                async with httpx.AsyncClient(timeout=timeout) as client:
                    headers = {"Content-Type": "application/json"}
                    
                    # Add authorization if token is provided
                    if settings.MODAL_TOKEN:
                        headers["Authorization"] = f"Bearer {settings.MODAL_TOKEN}"
                    
                    response = await client.post(
                        self.modal_url,
                        json={"image_b64": image_b64},
                        headers=headers
                    )
                    
                    # Check response status
                    if response.status_code == 200:
                        result = response.json()
                        extracted_text = result.get("text", "")
                        logger.info(f"Successfully extracted text: {len(extracted_text)} characters")
                        return extracted_text
                    else:
                        error_msg = f"Modal API returned status {response.status_code}: {response.text}"
                        logger.error(error_msg)
                        last_error = Exception(error_msg)
                        
                        # Don't retry on client errors (4xx)
                        if 400 <= response.status_code < 500:
                            raise last_error
                            
            except httpx.TimeoutException as e:
                last_error = Exception(f"Request timeout after {timeout}s. The model may be cold-starting.")
                logger.warning(f"Attempt {attempt + 1} timed out: {str(e)}")
                
            except httpx.RequestError as e:
                last_error = Exception(f"Network error: {str(e)}")
                logger.warning(f"Attempt {attempt + 1} failed with network error: {str(e)}")
                
            except Exception as e:
                last_error = e
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
            
            # Wait before retrying (exponential backoff)
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                logger.info(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
        
        # All retries failed
        error_message = f"Failed to process image after {max_retries} attempts"
        if last_error:
            error_message += f": {str(last_error)}"
        logger.error(error_message)
        raise Exception(error_message)
    
    async def extract_text(self, image_b64: str) -> Dict[str, any]:
        """
        Extract text from image
        
        Args:
            image_b64: Base64 encoded image string
            
        Returns:
            Dictionary with extracted text and metadata
        """
        start_time = time.time()
        
        try:
            # Validate image
            logger.info("Validating image...")
            image_bytes = self.validate_image(image_b64)
            logger.info(f"Image validated: {len(image_bytes)} bytes")
            
            # Process image with Modal API
            logger.info("Sending request to Modal API...")
            text = await self.process_with_modal(image_bytes)
            
            processing_time = time.time() - start_time
            logger.info(f"Text extraction completed in {processing_time:.2f}s")
            
            return {
                "text": text,
                "processing_time": processing_time,
                "confidence": None  # Add confidence calculation if available
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Text extraction failed after {processing_time:.2f}s: {str(e)}")
            raise

# Singleton instance
ocr_service = OCRService()
