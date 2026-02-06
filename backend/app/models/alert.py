from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.schemas.alert import AlertSeverity, AlertStatus, AlertRuleType, ComparisonOperator


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True, index=True)
    metric_type = Column(String(100), nullable=False)
    rule_type = Column(String(20), nullable=False)  # AlertRuleType
    severity = Column(String(20), nullable=False)  # AlertSeverity
    threshold_value = Column(Float)
    comparison_operator = Column(String(10))  # ComparisonOperator
    evaluation_window_minutes = Column(Integer, default=5)
    notification_channels = Column(JSON, default=list, nullable=False)  # List of NotificationChannel
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    device = relationship("Device", backref="alert_rules")
    alerts = relationship("Alert", backref="rule")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    metric_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)  # AlertSeverity
    status = Column(String(20), default="active", index=True)  # AlertStatus
    message = Column(Text, nullable=False)
    trigger_value = Column(Float, nullable=False)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    acknowledged_at = Column(DateTime(timezone=True))
    acknowledged_by = Column(String(255))
    resolved_at = Column(DateTime(timezone=True))
    snoozed_until = Column(DateTime(timezone=True))

    device = relationship("Device", backref="alerts")
