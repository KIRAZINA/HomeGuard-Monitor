from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class DeviceType(str, Enum):
    SERVER = "server"
    IOT_SENSOR = "iot_sensor"
    NETWORK_DEVICE = "network_device"
    CAMERA = "camera"
    OTHER = "other"


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    WARNING = "warning"
    ERROR = "error"


class DeviceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    device_type: DeviceType
    hostname: str = Field(..., min_length=1, max_length=255)
    ip_address: Optional[str] = Field(None, max_length=45)
    location: Optional[str] = Field(None, max_length=255)
    tags: Optional[str] = Field(None, max_length=500)


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    device_type: Optional[DeviceType] = None
    hostname: Optional[str] = Field(None, min_length=1, max_length=255)
    ip_address: Optional[str] = Field(None, max_length=45)
    location: Optional[str] = Field(None, max_length=255)
    tags: Optional[str] = Field(None, max_length=500)
    status: Optional[DeviceStatus] = None


class DeviceResponse(DeviceBase):
    id: int
    status: DeviceStatus
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
