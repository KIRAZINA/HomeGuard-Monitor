from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.schemas.alert import AlertRuleCreate, AlertRuleResponse, AlertResponse, AlertRuleUpdate
from app.services.alert_service import AlertService

router = APIRouter()


@router.post("/rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    rule: AlertRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    alert_service = AlertService(db)
    return await alert_service.create_alert_rule(rule)


@router.get("/rules", response_model=List[AlertRuleResponse])
async def list_alert_rules(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    alert_service = AlertService(db)
    return await alert_service.get_alert_rules(skip=skip, limit=limit)


@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: int,
    rule_update: AlertRuleUpdate,
    db: AsyncSession = Depends(get_db)
):
    alert_service = AlertService(db)
    rule = await alert_service.update_alert_rule(rule_id, rule_update)
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return rule


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db)
):
    alert_service = AlertService(db)
    success = await alert_service.delete_alert_rule(rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return {"message": "Alert rule deleted successfully"}


@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    skip: int = 0,
    limit: int = 100,
    acknowledged: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    alert_service = AlertService(db)
    return await alert_service.get_alerts(skip=skip, limit=limit, acknowledged=acknowledged)


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    alert_service = AlertService(db)
    success = await alert_service.acknowledge_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert acknowledged successfully"}


@router.post("/{alert_id}/snooze")
async def snooze_alert(
    alert_id: int,
    minutes: int = 30,
    db: AsyncSession = Depends(get_db)
):
    alert_service = AlertService(db)
    success = await alert_service.snooze_alert(alert_id, minutes)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": f"Alert snoozed for {minutes} minutes"}
