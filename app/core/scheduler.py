"""
Scheduler with retry mechanism
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from config.settings import settings

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _run_training_with_retry(db):
    from app.models.trainer.train_models import train_all_models
    train_all_models(db)
    logger.info("Training completed")

def scheduled_training():
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        _run_training_with_retry(db)
    except Exception as e:
        logger.error(f"Training failed: {e}")
    finally:
        db.close()

def init_scheduler():
    scheduler.add_job(scheduled_training, CronTrigger(day=1, hour=settings.TRAINING_SCHEDULE_HOUR), id='monthly_training', replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started")