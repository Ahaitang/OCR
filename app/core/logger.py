"""
Logger configuration - Console and file output
"""
import logging
import sys
from pathlib import Path
from config.settings import settings

def setup_logger() -> logging.Logger:
    logger = logging.getLogger(settings.SERVICE_NAME)
    logger.handlers.clear()
    log_level = logging.DEBUG if settings.DEBUG else getattr(logging, settings.LOG_LEVEL, logging.INFO)
    logger.setLevel(log_level)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_dir / f"{settings.SERVICE_NAME}.log", encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    error_handler = logging.FileHandler(log_dir / f"{settings.SERVICE_NAME}-error.log", encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    return logger

logger = setup_logger()