from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SNOOZED = "snoozed"


class AlertRuleType(str, Enum):
    THRESHOLD = "threshold"
    ANOMALY = "anomaly"


class ComparisonOperator(str, Enum):
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    GREATER_EQUAL = "gte"
    LESS_EQUAL = "lte"
    EQUAL = "eq"
    NOT_EQUAL = "ne"


class NotificationChannel(str, Enum):
    EMAIL = "email"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SMS = "sms"


class AlertRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    device_id: Optional[int] = None
    metric_type: str = Field(..., min_length=1, max_length=100)
    rule_type: AlertRuleType
    severity: AlertSeverity
    threshold_value: Optional[float] = None
    comparison_operator: Optional[ComparisonOperator] = None
    evaluation_window_minutes: int = Field(default=5, ge=1, le=1440)
    notification_channels: List[NotificationChannel] = []
    enabled: bool = True


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    device_id: Optional[int] = None
    metric_type: Optional[str] = Field(None, min_length=1, max_length=100)
    rule_type: Optional[AlertRuleType] = None
    severity: Optional[AlertSeverity] = None
    threshold_value: Optional[float] = None
    comparison_operator: Optional[ComparisonOperator] = None
    evaluation_window_minutes: Optional[int] = Field(None, ge=1, le=1440)
    notification_channels: Optional[List[NotificationChannel]] = None
    enabled: Optional[bool] = None


class AlertRuleResponse(AlertRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertBase(BaseModel):
    rule_id: int
    device_id: int
    metric_type: str
    severity: AlertSeverity
    message: str = Field(..., min_length=1, max_length=1000)
    trigger_value: float


class AlertCreate(AlertBase):
    pass


class AlertResponse(AlertBase):
    id: int
    status: AlertStatus
    triggered_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    snoozed_until: Optional[datetime] = None

    class Config:
        from_attributes = True
