from celery import current_app
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import structlog

from app.core.config import settings
from app.services.alert_service import AlertService
from app.services.metric_service import MetricService
from app.services.notification_service import NotificationService
from app.schemas.alert import AlertCreate

logger = structlog.get_logger()

# Create async session for Celery tasks
engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def evaluate_alert_rules_async():
    """Evaluate all active alert rules and trigger alerts if conditions are met"""
    async with AsyncSessionLocal() as db:
        alert_service = AlertService(db)
        metric_service = MetricService(db)
        notification_service = NotificationService()

        # Get all active alert rules
        rules = await alert_service.get_active_alert_rules()

        for rule in rules:
            try:
                await _evaluate_rule(rule, alert_service, metric_service, notification_service)
            except Exception as e:
                logger.error("Error evaluating alert rule", rule_id=rule.id, error=str(e))


@current_app.task
def evaluate_alert_rules():
    """Celery entrypoint for rule evaluation."""
    import asyncio
    asyncio.run(evaluate_alert_rules_async())


async def _evaluate_rule(rule, alert_service, metric_service, notification_service):
    """Evaluate a single alert rule"""
    rule_type = getattr(rule.rule_type, "value", rule.rule_type)
    comparison_operator = getattr(rule.comparison_operator, "value", rule.comparison_operator)
    if isinstance(rule_type, str) and "." in rule_type:
        rule_type = rule_type.split(".")[-1].lower()
    if isinstance(comparison_operator, str) and "." in comparison_operator:
        comparison_operator = comparison_operator.split(".")[-1].lower()

    # Get metrics for the evaluation window
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=rule.evaluation_window_minutes)
    
    from app.schemas.metric import MetricQuery
    query = MetricQuery(
        device_id=rule.device_id,
        metric_type=rule.metric_type,
        start_time=start_time,
        end_time=end_time,
        limit=100
    )
    
    metrics = await metric_service.get_metrics(query)
    
    if not metrics:
        return
    
    # Check if alert condition is met
    should_trigger = False
    trigger_value = None
    
    if rule_type == "threshold":
        latest_metric = metrics[0]  # Metrics are ordered by timestamp desc
        trigger_value = latest_metric.value
        
        if comparison_operator == "gt" and trigger_value > rule.threshold_value:
            should_trigger = True
        elif comparison_operator == "lt" and trigger_value < rule.threshold_value:
            should_trigger = True
        elif comparison_operator == "gte" and trigger_value >= rule.threshold_value:
            should_trigger = True
        elif comparison_operator == "lte" and trigger_value <= rule.threshold_value:
            should_trigger = True
        elif comparison_operator == "eq" and trigger_value == rule.threshold_value:
            should_trigger = True
        elif comparison_operator == "ne" and trigger_value != rule.threshold_value:
            should_trigger = True
    
    elif rule_type == "anomaly":
        # Simple anomaly detection using z-score
        import numpy as np
        values = [m.value for m in metrics]
        if len(values) > 5:  # Need sufficient data for anomaly detection
            mean = np.mean(values)
            std = np.std(values)
            if std > 0:
                z_scores = [abs((v - mean) / std) for v in values]
                max_index = int(np.argmax(z_scores))
                if z_scores[max_index] > 2.5:  # Threshold for anomaly
                    should_trigger = True
                    trigger_value = values[max_index]
                elif (max(values) - min(values)) > 20:
                    # Fallback heuristic to catch clear outliers
                    should_trigger = True
                    trigger_value = max(values)
    
    if should_trigger:
        # Check if there's already an active alert for this rule and device
        existing_alerts = await alert_service.get_alerts(
            acknowledged=False, limit=1
        )
        existing_alert = next(
            (a for a in existing_alerts 
             if a.rule_id == rule.id and a.device_id == rule.device_id and a.status == "active"),
            None
        )
        
        if not existing_alert:
            # Create new alert
            alert_data = AlertCreate(
                rule_id=rule.id,
                device_id=rule.device_id,
                metric_type=rule.metric_type,
                severity=rule.severity,
                message=f"Alert: {rule.name} - {rule.metric_type} is {trigger_value}",
                trigger_value=trigger_value
            )
            
            alert = await alert_service.create_alert(alert_data)
            
            # Send notifications
            await notification_service.send_alert_notifications(alert, rule)
            
            logger.info("Alert triggered", 
                       rule_id=rule.id, 
                       device_id=rule.device_id, 
                       alert_id=alert.id)
