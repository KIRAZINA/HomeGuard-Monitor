from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.schemas.metric import MetricCreate, MetricResponse, MetricQuery
from app.services.metric_service import MetricService

router = APIRouter()


@router.post("/ingest")
async def ingest_metrics(
    metrics: List[MetricCreate],
    db: AsyncSession = Depends(get_db)
):
    metric_service = MetricService(db)
    await metric_service.ingest_metrics(metrics)
    return {"message": f"Successfully ingested {len(metrics)} metrics"}


@router.get("/", response_model=List[MetricResponse])
async def get_metrics(
    device_id: Optional[int] = None,
    metric_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db)
):
    metric_service = MetricService(db)
    
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(hours=24)
    
    query = MetricQuery(
        device_id=device_id,
        metric_type=metric_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    
    return await metric_service.get_metrics(query)


@router.get("/device/{device_id}/latest")
async def get_latest_metrics(
    device_id: int,
    db: AsyncSession = Depends(get_db)
):
    metric_service = MetricService(db)
    metrics = await metric_service.get_latest_metrics(device_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="No metrics found for device")
    return metrics


@router.get("/device/{device_id}/summary")
async def get_metrics_summary(
    device_id: int,
    hours: int = 24,
    db: AsyncSession = Depends(get_db)
):
    metric_service = MetricService(db)
    summary = await metric_service.get_metrics_summary(device_id, hours)
    if not summary:
        raise HTTPException(status_code=404, detail="No metrics found for device")
    return summary
