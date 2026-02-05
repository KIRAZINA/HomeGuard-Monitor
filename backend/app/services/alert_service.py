from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from typing import List, Optional
from datetime import datetime, timedelta

from app.models.alert import AlertRule, Alert
from app.schemas.alert import AlertRuleCreate, AlertRuleUpdate, AlertCreate


class AlertService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_alert_rule(self, rule_data: AlertRuleCreate) -> AlertRule:
        rule = AlertRule(**rule_data.dict())
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def get_alert_rule(self, rule_id: int) -> Optional[AlertRule]:
        result = await self.db.execute(
            select(AlertRule).where(AlertRule.id == rule_id)
        )
        return result.scalar_one_or_none()

    async def get_alert_rules(
        self, skip: int = 0, limit: int = 100
    ) -> List[AlertRule]:
        result = await self.db.execute(
            select(AlertRule).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def update_alert_rule(
        self, rule_id: int, rule_data: AlertRuleUpdate
    ) -> Optional[AlertRule]:
        update_data = rule_data.dict(exclude_unset=True)
        if not update_data:
            return await self.get_alert_rule(rule_id)

        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.db.execute(
            update(AlertRule)
            .where(AlertRule.id == rule_id)
            .values(**update_data)
            .returning(AlertRule)
        )
        await self.db.commit()
        
        return result.scalar_one_or_none()

    async def delete_alert_rule(self, rule_id: int) -> bool:
        result = await self.db.execute(
            delete(AlertRule).where(AlertRule.id == rule_id)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def create_alert(self, alert_data: AlertCreate) -> Alert:
        alert = Alert(**alert_data.dict())
        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def get_alerts(
        self, skip: int = 0, limit: int = 100, acknowledged: Optional[bool] = None
    ) -> List[Alert]:
        conditions = []
        if acknowledged is not None:
            if acknowledged:
                conditions.append(Alert.status.in_(["acknowledged", "resolved"]))
            else:
                conditions.append(Alert.status == "active")
        
        stmt = (
            select(Alert)
            .where(and_(*conditions) if conditions else True)
            .order_by(Alert.triggered_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def acknowledge_alert(self, alert_id: int, acknowledged_by: str = "system") -> bool:
        result = await self.db.execute(
            update(Alert)
            .where(Alert.id == alert_id)
            .values(
                status="acknowledged",
                acknowledged_at=datetime.utcnow(),
                acknowledged_by=acknowledged_by
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    async def snooze_alert(self, alert_id: int, minutes: int = 30) -> bool:
        snooze_until = datetime.utcnow() + timedelta(minutes=minutes)
        result = await self.db.execute(
            update(Alert)
            .where(Alert.id == alert_id)
            .values(
                status="snoozed",
                snoozed_until=snooze_until
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    async def resolve_alert(self, alert_id: int) -> bool:
        result = await self.db.execute(
            update(Alert)
            .where(Alert.id == alert_id)
            .values(
                status="resolved",
                resolved_at=datetime.utcnow()
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    async def get_active_alert_rules(self) -> List[AlertRule]:
        result = await self.db.execute(
            select(AlertRule).where(AlertRule.enabled == True)
        )
        return result.scalars().all()
