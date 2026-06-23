from datetime import datetime

from pydantic import BaseModel, Field


class MetricBase(BaseModel):
    device_id: int
    metric_type: str = Field(..., min_length=1, max_length=100)
    value: int | float
    unit: str | None = Field(None, max_length=20)
    tags: dict | None = None


class MetricCreate(MetricBase):
    timestamp: datetime | None = None


class MetricResponse(MetricBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


class MetricQuery(BaseModel):
    device_id: int | None = None
    metric_type: str | None = None
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
