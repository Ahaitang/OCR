"""
Database connection management
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from config.settings import settings
from app.core.logger import logger

engine = create_engine(settings.database_url, pool_size=10, pool_recycle=3600, echo=settings.DEBUG, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database OK")
        return True
    except Exception as e:
        logger.error(f"Database failed: {e}")
        return False