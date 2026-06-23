"""Device schemas for request/response validation."""

from datetime import datetime
from enum import Enum
from typing import ClassVar

from pydantic import BaseModel, Field, validator


class DeviceType(str, Enum):
    """Supported device types."""

    SERVER = "server"
    IOT_SENSOR = "iot_sensor"
    NETWORK_DEVICE = "network_device"
    CAMERA = "camera"
    OTHER = "other"


class DeviceStatus(str, Enum):
    """Device operational status."""

    ONLINE = "online"
    OFFLINE = "offline"
    WARNING = "warning"
    ERROR = "error"


class DeviceBase(BaseModel):
    """Base device data."""

    name: str = Field(..., min_length=1, max_length=255, description="Device name")
    description: str | None = Field(None, max_length=500, description="Device description")
    device_type: DeviceType = Field(..., description="Device type")
    hostname: str = Field(..., min_length=1, max_length=255, description="Device hostname")
    ip_address: str | None = Field(None, max_length=45, description="Device IP address")
    location: str | None = Field(None, max_length=255, description="Physical device location")
    tags: list[str] | None = Field(default_factory=list, description="Device tags for organization")

    @validator("hostname")
    def validate_hostname(cls, v: str) -> str:
        """Validate hostname format."""
        if not v.replace(".", "").replace("-", "").replace("_", "").isalnum():
            raise ValueError("Invalid hostname format")
        return v

    @validator("ip_address")
    def validate_ip(cls, v: str | None) -> str | None:
        """Validate IP address format."""
        if v is None:
            return v
        parts = v.split(".")
        if len(parts) != 4:
            raise ValueError("Invalid IPv4 address")
        for part in parts:
            try:
                num = int(part)
                if not 0 <= num <= 255:
                    raise ValueError("Invalid IPv4 address")
            except ValueError:
                raise ValueError("Invalid IPv4 address") from None
        return v


class DeviceCreate(DeviceBase):
    """Device creation request."""

    pass


class DeviceUpdate(BaseModel):
    """Device update request."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=500)
    device_type: DeviceType | None = None
    hostname: str | None = Field(None, min_length=1, max_length=255)
    ip_address: str | None = Field(None, max_length=45)
    location: str | None = Field(None, max_length=255)
    tags: list[str] | None = None
    status: DeviceStatus | None = None

    @validator("hostname")
    def validate_hostname(cls, v: str | None) -> str | None:
        """Validate hostname format."""
        if v is None:
            return v
        if not v.replace(".", "").replace("-", "").replace("_", "").isalnum():
            raise ValueError("Invalid hostname format")
        return v


class DeviceResponse(DeviceBase):
    """Device response model."""

    id: int = Field(..., description="Device ID")
    api_key: str | None = Field(None, description="Agent API key (only returned on creation)")
    status: DeviceStatus = Field(..., description="Device status")
    last_seen: datetime | None = Field(None, description="Last seen timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        """Pydantic config."""

        from_attributes = True
        json_encoders: ClassVar[dict] = {
            datetime: lambda v: v.isoformat() if v else None,
            DeviceType: lambda v: v.value,
            DeviceStatus: lambda v: v.value,
        }
