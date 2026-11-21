"""
Application Configuration
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "OCR Service API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from comma-separated string or list"""
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    # Model Configuration
    HF_REPO_ID: str = "KuongB/glm-ocr-vietnamese"  # Reference only
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Modal API Configuration
    MODAL_API_URL: str = ""
    MODAL_TOKEN: str = ""
    MODAL_TIMEOUT: int = 60  # Timeout in seconds for Modal API calls
    MODAL_MAX_RETRIES: int = 3  # Number of retries for failed requests
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
