from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from app.core.database import Base
from app.schemas.device import DeviceType, DeviceStatus


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    device_type = Column(SQLEnum(DeviceType), nullable=False)
    hostname = Column(String(255), nullable=False)
    ip_address = Column(String(45))
    location = Column(String(255))
    tags = Column(String(500))
    status = Column(SQLEnum(DeviceStatus), default=DeviceStatus.OFFLINE)
    last_seen = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
