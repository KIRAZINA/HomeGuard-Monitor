from pydantic import BaseModel, Field
from typing import Optional, Union
from datetime import datetime


class MetricBase(BaseModel):
    device_id: int
    metric_type: str = Field(..., min_length=1, max_length=100)
    value: Union[int, float]
    unit: Optional[str] = Field(None, max_length=20)
    tags: Optional[dict] = None


class MetricCreate(MetricBase):
    timestamp: Optional[datetime] = None


class MetricResponse(MetricBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


class MetricQuery(BaseModel):
    device_id: Optional[int] = None
    metric_type: Optional[str] = None
    start_time: datetime
    end_time: datetime
    limit: int = Field(default=1000, le=10000)


class MetricSummary(BaseModel):
    device_id: int
    metric_type: str
    count: int
    min_value: float
    max_value: float
    avg_value: float
    latest_value: float
    latest_timestamp: datetime
