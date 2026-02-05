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


@current_app.task
def cleanup_old_metrics():
    """Clean up metrics older than the retention period"""
    import asyncio
    
    async def _cleanup():
        async with AsyncSessionLocal() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=settings.METRICS_RETENTION_DAYS)
            
            # Delete old metrics
            stmt = delete(Metric).where(Metric.timestamp < cutoff_date)
            result = await db.execute(stmt)
            await db.commit()
            
            logger.info("Cleaned up old metrics", deleted_count=result.rowcount)
    
    asyncio.run(_cleanup())


@current_app.task
def aggregate_metrics():
    """Aggregate metrics into hourly/daily summaries"""
    import asyncio
    
    async def _aggregate():
        async with AsyncSessionLocal() as db:
            # This is a placeholder for metric aggregation
            # In a real implementation, you would create summary tables
            # and populate them with aggregated data
            logger.info("Metric aggregation task completed")
    
    asyncio.run(_aggregate())
