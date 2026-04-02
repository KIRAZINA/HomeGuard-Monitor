"""Device data model."""
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum, Index, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base
from app.schemas.device import DeviceType, DeviceStatus


class Device(Base):
    """Device model."""
    __tablename__ = "devices"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Basic information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    device_type = Column(SQLEnum(DeviceType), nullable=False, index=True)
    
    # Connection details
    hostname = Column(String(255), nullable=False, unique=True, index=True)
    ip_address = Column(String(45), nullable=True, index=True)
    
    # Organization
    location = Column(String(255), nullable=True)
    tags = Column(String(500), nullable=True)
    
    # Status tracking
    status = Column(
        SQLEnum(DeviceStatus),
        nullable=False,
        default=DeviceStatus.OFFLINE,
        index=True,
    )
    last_seen = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
    )
    
    # Composite indexes for common queries
    __table_args__ = (
        Index("idx_device_status_updated", "status", "updated_at"),
        Index("idx_device_type_status", "device_type", "status"),
        UniqueConstraint("hostname", name="uq_device_hostname"),
    )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<Device(id={self.id}, name={self.name}, hostname={self.hostname}, status={self.status})>"

