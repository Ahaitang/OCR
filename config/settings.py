"""
Centralized configuration management with validation
"""
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv(Path(__file__).parent / '.env')


class ConfigError(Exception):
    """Configuration validation error"""
    pass


class Settings:
    """Application settings with validation"""

    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "QMG")

    # Service
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "hospital-api")
    SERVICE_VERSION: str = os.getenv("SERVICE_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # API Authentication
    API_KEY: str = os.getenv("API_KEY", "")
    API_KEY_ENABLED: bool = os.getenv("API_KEY_ENABLED", "true").lower() == "true"

    # CORS
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8080"
    ).split(",")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")

    # OCR
    MAX_IMAGE_SIZE_MB: int = int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))

    # Training
    MIN_TRAINING_RECORDS: int = 50
    TRAINING_SCHEDULE_HOUR: int = int(os.getenv("TRAINING_SCHEDULE_HOUR", "3"))

    # Model paths
    MODEL_DIR: Path = Path(__file__).parent.parent / "app" / "models" / "pretrained"

    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    def validate(self) -> None:
        """Validate critical configuration"""
        errors = []
        if self.API_KEY_ENABLED and not self.API_KEY and not self.DEBUG:
            errors.append("API_KEY must be set when API_KEY_ENABLED=true (production)")
        if errors:
            raise ConfigError("Configuration validation failed:\n" + "\n".join(errors))


settings = Settings()
if os.getenv("SKIP_CONFIG_VALIDATION", "false").lower() != "true":
    try:
        settings.validate()
    except ConfigError as e:
        print(f"WARNING: {e}")