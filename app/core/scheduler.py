"""
Scheduler - Monthly model training
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from app.core.database import SessionLocal
from app.models.trainer.train_models import train_all_models

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def init_scheduler():
    """Initialize scheduled tasks"""
    scheduler.add_job(
        scheduled_training,
        CronTrigger(day=1, hour=3, minute=0),
        id='monthly_training',
        replace_existing=True
    )
    scheduler.start()
    logger.info("Scheduler started - monthly training scheduled")


def scheduled_training():
    """Run scheduled training"""
    db = SessionLocal()
    try:
        train_all_models(db)
    except Exception as e:
        logger.error(f"Training failed: {e}")
    finally:
        db.close()