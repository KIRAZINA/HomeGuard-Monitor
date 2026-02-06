from celery import current_app
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import delete, and_
from datetime import datetime, timedelta
import structlog

from app.core.config import settings
from app.models.metric import Metric

logger = structlog.get_logger()

# Create async session for Celery tasks
engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def cleanup_old_metrics_async():
    """Clean up metrics older than the retention period."""
    async with AsyncSessionLocal() as db:
        cutoff_date = datetime.utcnow() - timedelta(days=settings.METRICS_RETENTION_DAYS)

        # Delete old metrics
        stmt = delete(Metric).where(Metric.timestamp < cutoff_date)
        result = await db.execute(stmt)
        await db.commit()

        logger.info("Cleaned up old metrics", deleted_count=result.rowcount)


@current_app.task
def cleanup_old_metrics():
    """Celery entrypoint for cleanup."""
    import asyncio
    asyncio.run(cleanup_old_metrics_async())


async def aggregate_metrics_async():
    """Aggregate metrics into hourly/daily summaries."""
    async with AsyncSessionLocal() as db:
        # This is a placeholder for metric aggregation
        # In a real implementation, you would create summary tables
        # and populate them with aggregated data
        logger.info("Metric aggregation task completed")


@current_app.task
def aggregate_metrics():
    """Celery entrypoint for aggregation."""
    import asyncio
    asyncio.run(aggregate_metrics_async())
