"""Celery tasks for alert rule evaluation."""
from celery import current_app
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import structlog
import numpy as np

from app.core.config import settings
from app.core.database import SyncSessionLocal
from app.models.alert import AlertRule, Alert
from app.models.metric import Metric
from app.schemas.alert import AlertSeverity, AlertStatus, AlertRuleType, ComparisonOperator

logger = structlog.get_logger()


@current_app.task
def evaluate_alert_rules():
    """Evaluate all active alert rules and trigger alerts if conditions are met."""
    db: Session = SyncSessionLocal()
    try:
        rules = db.query(AlertRule).filter(AlertRule.enabled == True).all()

        for rule in rules:
            try:
                _evaluate_rule(db, rule)
            except Exception as e:
                logger.error("Error evaluating alert rule", rule_id=rule.id, error=str(e))
    finally:
        db.close()


def _evaluate_rule(db: Session, rule: AlertRule):
    """Evaluate a single alert rule."""
    rule_type = getattr(rule.rule_type, "value", rule.rule_type)
    comparison_operator = getattr(rule.comparison_operator, "value", rule.comparison_operator)
    if isinstance(rule_type, str) and "." in rule_type:
        rule_type = rule_type.split(".")[-1].lower()
    if isinstance(comparison_operator, str) and "." in comparison_operator:
        comparison_operator = comparison_operator.split(".")[-1].lower()

    # Get metrics for the evaluation window
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=rule.evaluation_window_minutes)

    metrics = (
        db.query(Metric)
        .filter(
            Metric.device_id == rule.device_id,
            Metric.metric_type == rule.metric_type,
            Metric.timestamp >= start_time,
            Metric.timestamp <= end_time,
        )
        .order_by(Metric.timestamp.desc())
        .limit(100)
        .all()
    )

    if not metrics:
        return

    # Check if alert condition is met
    should_trigger = False
    trigger_value = None

    if rule_type == "threshold":
        latest_metric = metrics[0]
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
        values = [m.value for m in metrics]
        if len(values) > 5:
            mean = np.mean(values)
            std = np.std(values)
            if std > 0:
                z_scores = [abs((v - mean) / std) for v in values]
                max_index = int(np.argmax(z_scores))
                if z_scores[max_index] > 2.5:
                    should_trigger = True
                    trigger_value = values[max_index]
                elif (max(values) - min(values)) > 20:
                    should_trigger = True
                    trigger_value = max(values)

    if should_trigger:
        # Check if there's already an active alert for this rule and device
        existing_alert = (
            db.query(Alert)
            .filter(
                Alert.rule_id == rule.id,
                Alert.device_id == rule.device_id,
                Alert.status == "active",
            )
            .first()
        )

        if not existing_alert:
            alert = Alert(
                rule_id=rule.id,
                device_id=rule.device_id,
                metric_type=rule.metric_type,
                severity=rule.severity,
                status="active",
                message=f"Alert: {rule.name} - {rule.metric_type} is {trigger_value}",
                trigger_value=trigger_value,
                triggered_at=datetime.utcnow(),
            )
            db.add(alert)
            db.commit()

            logger.info(
                "Alert triggered",
                rule_id=rule.id,
                device_id=rule.device_id,
                alert_id=alert.id,
            )
