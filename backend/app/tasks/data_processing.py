"""Celery tasks for data processing and maintenance."""

from celery import current_app
from datetime import datetime, timedelta
import structlog

from app.core.config import settings
from app.core.database import SyncSessionLocal
from app.models.metric import Metric

logger = structlog.get_logger()


@current_app.task
def cleanup_old_metrics():
    """Clean up metrics older than the retention period."""
    db = SyncSessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=settings.METRICS_RETENTION_DAYS)

        deleted = db.query(Metric).filter(Metric.timestamp < cutoff_date).delete()
        db.commit()

        logger.info("Cleaned up old metrics", deleted_count=deleted)
    finally:
        db.close()


@current_app.task
def aggregate_metrics():
    """Aggregate metrics into hourly/daily summaries.

    Note: TimescaleDB continuous aggregates handle the actual aggregation
    at the database level. This task is a placeholder for any additional
    application-level aggregation logic.
    """
    logger.info("Metric aggregation task completed")
