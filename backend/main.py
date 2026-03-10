"""
Main application entry point
"""

import uvicorn
import logging
from app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger(__name__)

app = create_app()

if __name__ == "__main__":
    logger.info("🚀 Starting OCR Service API...")
    logger.info("📚 API Documentation: http://localhost:8000/api/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
