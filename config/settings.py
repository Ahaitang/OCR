"""
OCR Service Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)


class Settings:
    """OCR Service settings"""

    # Service
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "hospital-ocr")
    SERVICE_VERSION: str = os.getenv("SERVICE_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")

    # OCR
    MAX_IMAGE_SIZE_MB: int = int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))


settings = Settings()