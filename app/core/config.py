"""
Configuration management
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings"""

    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "hospital")

    # Service
    SERVICE_NAME: str = "hospital-ai-service"
    SERVICE_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # API Authentication
    API_KEY: str = os.getenv("API_KEY", "")
    API_KEY_ENABLED: bool = os.getenv("API_KEY_ENABLED", "true").lower() == "true"

    # CORS - configurable allowed origins
    ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")

    # Models
    MODEL_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "models", "pretrained"
    )

    # Training
    MIN_TRAINING_RECORDS: int = 50
    TRAINING_SCHEDULE_HOUR: int = 3  # 3 AM on 1st of each month

    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()