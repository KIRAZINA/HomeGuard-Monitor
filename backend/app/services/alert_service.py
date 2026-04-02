"""Alert service for managing alert rules and alerts."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, func
from typing import List, Optional
from datetime import datetime, timedelta
import structlog

from app.models.alert import AlertRule, Alert
from app.schemas.alert import AlertRuleCreate, AlertRuleUpdate, AlertCreate
from app.core.exceptions import NotFoundError, DatabaseError

logger = structlog.get_logger()


class AlertService:
    """Service for managing alert rules and triggered alerts."""
    
    def __init__(self, db: AsyncSession) -> None:
        """Initialize service with database session.
        
        Args:
            db: AsyncSession database session
        """
        self.db = db
    
    async def create_alert_rule(self, rule_data: AlertRuleCreate) -> AlertRule:
        """Create a new alert rule.
        
        Args:
            rule_data: Alert rule creation data
            
        Returns:
            Created alert rule
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            rule = AlertRule(**rule_data.model_dump(mode="json"))
            self.db.add(rule)
            await self.db.commit()
            await self.db.refresh(rule)
            
            logger.info(
                "alert_rule_created",
                rule_id=rule.id,
                device_id=rule.device_id,
            )
            return rule
        except Exception as e:
            logger.exception("create_alert_rule_failed", exc_info=e)
            await self.db.rollback()
            raise DatabaseError("Failed to create alert rule")
    
    async def get_alert_rule(self, rule_id: int) -> Optional[AlertRule]:
        """Get alert rule by ID.
        
        Args:
            rule_id: Alert rule ID
            
        Returns:
            Alert rule or None
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            result = await self.db.execute(
                select(AlertRule).where(AlertRule.id == rule_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.exception("get_alert_rule_failed", rule_id=rule_id, exc_info=e)
            raise DatabaseError("Failed to get alert rule")
    
    async def get_alert_rules(
        self,
        skip: int = 0,
        limit: int = 100,
        device_id: Optional[int] = None,
        enabled_only: bool = False,
    ) -> List[AlertRule]:
        """Get paginated alert rules with optional filters.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            device_id: Filter by device ID
            enabled_only: Only return enabled rules
            
        Returns:
            List of alert rules
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = select(AlertRule)
            
            if device_id is not None:
                query = query.where(AlertRule.device_id == device_id)
            if enabled_only:
                query = query.where(AlertRule.enabled.is_(True))
            
            query = query.order_by(AlertRule.created_at.desc()).offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.exception("get_alert_rules_failed", exc_info=e)
            raise DatabaseError("Failed to retrieve alert rules")
    
    async def update_alert_rule(
        self,
        rule_id: int,
        rule_data: AlertRuleUpdate,
    ) -> Optional[AlertRule]:
        """Update an alert rule.
        
        Args:
            rule_id: Alert rule ID
            rule_data: Updated rule data
            
        Returns:
            Updated alert rule or None
            
        Raises:
            NotFoundError: If rule not found
            DatabaseError: If database operation fails
        """
        try:
            rule = await self.get_alert_rule(rule_id)
            if not rule:
                raise NotFoundError("Alert rule")
            
            update_data = rule_data.model_dump(exclude_unset=True, mode="json")
            if not update_data:
                return rule
            
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.db.execute(
                update(AlertRule)
                .where(AlertRule.id == rule_id)
                .values(**update_data)
                .returning(AlertRule)
            )
            await self.db.commit()
            
            updated = result.scalar_one_or_none()
            logger.info("alert_rule_updated", rule_id=rule_id)
            return updated
        except NotFoundError:
            raise
        except Exception as e:
            logger.exception("update_alert_rule_failed", rule_id=rule_id, exc_info=e)
            await self.db.rollback()
            raise DatabaseError("Failed to update alert rule")
    
    async def delete_alert_rule(self, rule_id: int) -> bool:
        """Delete an alert rule.
        
        Args:
            rule_id: Alert rule ID
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            result = await self.db.execute(
                delete(AlertRule).where(AlertRule.id == rule_id)
            )
            await self.db.commit()
            deleted = result.rowcount > 0
            
            if deleted:
                logger.info("alert_rule_deleted", rule_id=rule_id)
            
            return deleted
        except Exception as e:
            logger.exception("delete_alert_rule_failed", rule_id=rule_id, exc_info=e)
            await self.db.rollback()
            raise DatabaseError("Failed to delete alert rule")
    
    async def create_alert(self, alert_data: AlertCreate) -> Alert:
        """Create a new alert instance.
        
        Args:
            alert_data: Alert creation data
            
        Returns:
            Created alert
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            alert = Alert(**alert_data.model_dump(mode="json"))
            self.db.add(alert)
            await self.db.commit()
            await self.db.refresh(alert)
            
            logger.info(
                "alert_created",
                alert_id=alert.id,
                rule_id=alert.rule_id,
                severity=alert.severity,
            )
            return alert
        except Exception as e:
            logger.exception("create_alert_failed", exc_info=e)
            await self.db.rollback()
            raise DatabaseError("Failed to create alert")
    
    async def get_alerts(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        hours: int = 24,
    ) -> List[Alert]:
        """Get paginated alerts with optional filters.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            status: Filter by alert status
            severity: Filter by severity level
            hours: Only return alerts from last N hours
            
        Returns:
            List of alerts
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            conditions = []
            
            if status:
                conditions.append(Alert.status == status)
            if severity:
                conditions.append(Alert.severity == severity)
            
            # Filter by time window
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            conditions.append(Alert.triggered_at >= cutoff_time)
            
            stmt = (
                select(Alert)
                .where(and_(*conditions) if conditions else True)
                .order_by(Alert.triggered_at.desc())
                .offset(skip)
                .limit(limit)
            )
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.exception("get_alerts_failed", exc_info=e)
            raise DatabaseError("Failed to retrieve alerts")
    
    async def get_alerts_count(
        self,
        status: Optional[str] = None,
        hours: int = 24,
    ) -> int:
        """Get count of alerts.
        
        Args:
            status: Filter by status
            hours: Only count alerts from last N hours
            
        Returns:
            Alert count
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            conditions = []
            
            if status:
                conditions.append(Alert.status == status)
            
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            conditions.append(Alert.triggered_at >= cutoff_time)
            
            result = await self.db.execute(
                select(func.count(Alert.id)).where(
                    and_(*conditions) if conditions else True
                )
            )
            return result.scalar() or 0
        except Exception as e:
            logger.exception("get_alerts_count_failed", exc_info=e)
            raise DatabaseError("Failed to count alerts")
    
    async def acknowledge_alert(
        self,
        alert_id: int,
        acknowledged_by: str = "system",
    ) -> bool:
        """Acknowledge an alert.
        
        Args:
            alert_id: Alert ID
            acknowledged_by: User or system that acknowledged
            
        Returns:
            True if updated, False if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            result = await self.db.execute(
                update(Alert)
                .where(Alert.id == alert_id)
                .values(
                    status="acknowledged",
                    acknowledged_at=datetime.utcnow(),
                    acknowledged_by=acknowledged_by,
                )
            )
            await self.db.commit()
            updated = result.rowcount > 0
            
            if updated:
                logger.info(
                    "alert_acknowledged",
                    alert_id=alert_id,
                    acknowledged_by=acknowledged_by,
                )
            
            return updated
        except Exception as e:
            logger.exception("acknowledge_alert_failed", alert_id=alert_id, exc_info=e)
            await self.db.rollback()
            raise DatabaseError("Failed to acknowledge alert")
    
    async def resolve_alert(
        self,
        alert_id: int,
        resolved_by: str = "system",
    ) -> bool:
        """Resolve an alert.
        
        Args:
            alert_id: Alert ID
            resolved_by: User or system that resolved
            
        Returns:
            True if updated, False if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            result = await self.db.execute(
                update(Alert)
                .where(Alert.id == alert_id)
                .values(
                    status="resolved",
                    resolved_at=datetime.utcnow(),
                    resolved_by=resolved_by,
                )
            )
            await self.db.commit()
            updated = result.rowcount > 0
            
            if updated:
                logger.info(
                    "alert_resolved",
                    alert_id=alert_id,
                    resolved_by=resolved_by,
                )
            
            return updated
        except Exception as e:
            logger.exception("resolve_alert_failed", alert_id=alert_id, exc_info=e)
            await self.db.rollback()
            raise DatabaseError("Failed to resolve alert")


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
