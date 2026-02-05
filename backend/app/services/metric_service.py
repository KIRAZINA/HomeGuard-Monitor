from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from datetime import datetime, timedelta

from app.models.metric import Metric
from app.schemas.metric import MetricCreate, MetricQuery, MetricSummary


class MetricService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def ingest_metrics(self, metrics_data: List[MetricCreate]) -> None:
        metrics = []
        for metric_data in metrics_data:
            if not metric_data.timestamp:
                metric_data.timestamp = datetime.utcnow()
            metrics.append(Metric(**metric_data.dict()))
        
        self.db.add_all(metrics)
        await self.db.commit()

    async def get_metrics(self, query: MetricQuery) -> List[Metric]:
        conditions = []
        
        if query.device_id:
            conditions.append(Metric.device_id == query.device_id)
        if query.metric_type:
            conditions.append(Metric.metric_type == query.metric_type)
        
        conditions.append(
            and_(
                Metric.timestamp >= query.start_time,
                Metric.timestamp <= query.end_time
            )
        )
        
        stmt = (
            select(Metric)
            .where(and_(*conditions))
            .order_by(Metric.timestamp.desc())
            .limit(query.limit)
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_latest_metrics(self, device_id: int) -> List[Metric]:
        subquery = (
            select(
                Metric.metric_type,
                func.max(Metric.timestamp).label('latest_timestamp')
            )
            .where(Metric.device_id == device_id)
            .group_by(Metric.metric_type)
            .subquery()
        )
        
        stmt = (
            select(Metric)
            .join(
                subquery,
                and_(
                    Metric.metric_type == subquery.c.metric_type,
                    Metric.timestamp == subquery.c.latest_timestamp
                )
            )
            .where(Metric.device_id == device_id)
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_metrics_summary(
        self, device_id: int, hours: int = 24
    ) -> List[MetricSummary]:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        stmt = (
            select(
                Metric.device_id,
                Metric.metric_type,
                func.count(Metric.id).label('count'),
                func.min(Metric.value).label('min_value'),
                func.max(Metric.value).label('max_value'),
                func.avg(Metric.value).label('avg_value')
            )
            .where(
                and_(
                    Metric.device_id == device_id,
                    Metric.timestamp >= start_time
                )
            )
            .group_by(Metric.device_id, Metric.metric_type)
        )
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        summaries = []
        for row in rows:
            latest_metric = await self.get_latest_metric_value(
                device_id, row.metric_type
            )
            
            summary = MetricSummary(
                device_id=row.device_id,
                metric_type=row.metric_type,
                count=row.count,
                min_value=float(row.min_value),
                max_value=float(row.max_value),
                avg_value=float(row.avg_value),
                latest_value=latest_metric.value if latest_metric else 0.0,
                latest_timestamp=latest_metric.timestamp if latest_metric else datetime.utcnow()
            )
            summaries.append(summary)
        
        return summaries

    async def get_latest_metric_value(
        self, device_id: int, metric_type: str
    ) -> Optional[Metric]:
        stmt = (
            select(Metric)
            .where(
                and_(
                    Metric.device_id == device_id,
                    Metric.metric_type == metric_type
                )
            )
            .order_by(Metric.timestamp.desc())
            .limit(1)
        )
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
