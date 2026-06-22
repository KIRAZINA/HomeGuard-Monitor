from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.auth import get_current_active_user, verify_agent_api_key
from app.schemas.metric import MetricCreate, MetricResponse, MetricQuery
from app.services.metric_service import MetricService
from app.models.user import User
from app.models.device import Device

router = APIRouter()


@router.post("/ingest")
async def ingest_metrics(
    metrics: List[MetricCreate],
    db: AsyncSession = Depends(get_db),
    device: Device = Depends(verify_agent_api_key),
):
    # Override device_id with the authenticated device
    for metric in metrics:
        metric.device_id = device.id
    metric_service = MetricService(db)
    result = await metric_service.ingest_metrics(metrics)
    return {"message": f"Successfully ingested {result['ingested']} metrics"}


@router.get("/", response_model=List[MetricResponse])
async def get_metrics(
    device_id: Optional[int] = None,
    metric_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    metric_service = MetricService(db)
    summary = await metric_service.get_metrics_summary(device_id, hours)
    if not summary:
        raise HTTPException(status_code=404, detail="No metrics found for device")
    return summary
