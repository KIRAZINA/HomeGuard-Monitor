"""Device service for database operations."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
import structlog

from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError

logger = structlog.get_logger()


class DeviceService:
    """Service for managing devices."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service with database session.

        Args:
            db: AsyncSession database session
        """
        self.db = db

    async def create_device(self, device_data: DeviceCreate, user_id: int) -> Device:
        """Create a new device.

        Args:
            device_data: Device creation data
            user_id: Owner user ID

        Returns:
            Created device instance

        Raises:
            DuplicateError: If device with same hostname exists
            DatabaseError: If database operation fails
        """
        try:
            # Check for duplicate hostname
            existing = await self._get_by_hostname(device_data.hostname)
            if existing:
                raise DuplicateError(
                    f"Device with hostname '{device_data.hostname}'",
                    details={"hostname": device_data.hostname},
                )

            # Create device with ownership
            device_data_dict = device_data.model_dump()
            device_data_dict["user_id"] = user_id
            # Convert tags list to comma-separated string for storage
            if "tags" in device_data_dict:
                tags = device_data_dict.pop("tags", None)
                if tags:
                    device_data_dict["tags"] = (
                        ",".join(tags) if isinstance(tags, list) else str(tags)
                    )
                else:
                    device_data_dict["tags"] = None
            device = Device(**device_data_dict)
            self.db.add(device)
            await self.db.commit()
            await self.db.refresh(device)

            logger.info(
                "device_created",
                device_id=device.id,
                name=device.name,
                hostname=device.hostname,
                user_id=user_id,
            )
            return device
        except DuplicateError:
            raise
        except Exception as e:
            logger.exception("create_device_failed", exc_info=e)
            await self.db.rollback()
            raise DatabaseError("Failed to create device", {"error": str(e)})

    async def get_device(self, device_id: int, user_id: int) -> Optional[Device]:
        """Get device by ID scoped to user.

        Args:
            device_id: Device ID
            user_id: Owner user ID

        Returns:
            Device instance or None

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            result = await self.db.execute(
                select(Device).where(
                    Device.id == device_id,
                    Device.user_id == user_id,
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.exception("get_device_failed", device_id=device_id, exc_info=e)
            raise DatabaseError(f"Failed to get device {device_id}")

    async def get_devices(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        device_type: Optional[str] = None,
    ) -> List[Device]:
        """Get paginated devices list scoped to user.

        Args:
            user_id: Owner user ID
            skip: Number of records to skip
            limit: Maximum records to return
            status: Filter by device status
            device_type: Filter by device type

        Returns:
            List of devices

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = select(Device).where(Device.user_id == user_id)

            if status:
                query = query.where(Device.status == status)
            if device_type:
                query = query.where(Device.device_type == device_type)

            query = query.order_by(Device.created_at.desc()).offset(skip).limit(limit)

            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.exception("get_devices_failed", skip=skip, limit=limit, exc_info=e)
            raise DatabaseError("Failed to retrieve devices")

    async def get_devices_count(self, user_id: int) -> int:
        """Get count of user's devices.

        Args:
            user_id: Owner user ID

        Returns:
            Device count

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            result = await self.db.execute(
                select(func.count(Device.id)).where(Device.user_id == user_id)
            )
            return result.scalar() or 0
        except Exception as e:
            logger.exception("get_devices_count_failed", exc_info=e)
            raise DatabaseError("Failed to count devices")

    async def update_device(
        self,
        device_id: int,
        device_data: DeviceUpdate,
        user_id: int,
    ) -> Optional[Device]:
        """Update a device scoped to user.

        Args:
            device_id: Device ID to update
            device_data: Updated device data
            user_id: Owner user ID

        Returns:
            Updated device instance or None

        Raises:
            NotFoundError: If device not found
            DuplicateError: If updating hostname to existing one
            DatabaseError: If database operation fails
        """
        try:
            device = await self.get_device(device_id, user_id)
            if not device:
                raise NotFoundError("Device")

            update_data = device_data.model_dump(exclude_unset=True)
            if not update_data:
                return device
            # Convert tags list to comma-separated string
            if "tags" in update_data:
                tags = update_data.pop("tags")
                if tags:
                    update_data["tags"] = ",".join(tags) if isinstance(tags, list) else str(tags)
                else:
                    update_data["tags"] = None

            # Check for hostname collision
            if "hostname" in update_data and update_data["hostname"] != device.hostname:
                existing = await self._get_by_hostname(update_data["hostname"])
                if existing:
                    raise DuplicateError(
                        f"Device with hostname '{update_data['hostname']}'",
                        details={"hostname": update_data["hostname"]},
                    )

            update_data["updated_at"] = datetime.utcnow()

            result = await self.db.execute(
                update(Device).where(Device.id == device_id).values(**update_data).returning(Device)
            )
            await self.db.commit()

            updated_device = result.scalar_one_or_none()
            logger.info("device_updated", device_id=device_id)
            return updated_device
        except (NotFoundError, DuplicateError):
            raise
        except Exception as e:
            logger.exception("update_device_failed", device_id=device_id, exc_info=e)
            await self.db.rollback()
            raise DatabaseError(f"Failed to update device {device_id}")

    async def delete_device(self, device_id: int, user_id: int) -> bool:
        """Delete a device scoped to user.

        Args:
            device_id: Device ID to delete
            user_id: Owner user ID

        Returns:
            True if deleted, False if not found

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            result = await self.db.execute(
                delete(Device).where(
                    Device.id == device_id,
                    Device.user_id == user_id,
                )
            )
            await self.db.commit()
            deleted = result.rowcount > 0

            if deleted:
                logger.info("device_deleted", device_id=device_id)

            return deleted
        except Exception as e:
            logger.exception("delete_device_failed", device_id=device_id, exc_info=e)
            await self.db.rollback()
            raise DatabaseError(f"Failed to delete device {device_id}")

    async def update_device_status(
        self,
        device_id: int,
        status: str,
    ) -> bool:
        """Update device status.

        Args:
            device_id: Device ID
            status: New status

        Returns:
            True if updated, False if not found

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            result = await self.db.execute(
                update(Device)
                .where(Device.id == device_id)
                .values(
                    status=status,
                    last_seen=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )
            await self.db.commit()
            updated = result.rowcount > 0

            if updated:
                logger.info(
                    "device_status_updated",
                    device_id=device_id,
                    status=status,
                )

            return updated
        except Exception as e:
            logger.exception(
                "update_device_status_failed",
                device_id=device_id,
                exc_info=e,
            )
            await self.db.rollback()
            raise DatabaseError(f"Failed to update device status {device_id}")

    async def _get_by_hostname(self, hostname: str) -> Optional[Device]:
        """Get device by hostname (internal method).

        Args:
            hostname: Device hostname

        Returns:
            Device instance or None
        """
        result = await self.db.execute(select(Device).where(Device.hostname == hostname))
        return result.scalar_one_or_none()
