from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse


class DeviceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_device(self, device_data: DeviceCreate) -> Device:
        device = Device(**device_data.model_dump())
        self.db.add(device)
        await self.db.commit()
        await self.db.refresh(device)
        return device

    async def get_device(self, device_id: int) -> Optional[Device]:
        result = await self.db.execute(
            select(Device).where(Device.id == device_id)
        )
        return result.scalar_one_or_none()

    async def get_devices(self, skip: int = 0, limit: int = 100) -> List[Device]:
        result = await self.db.execute(
            select(Device).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def update_device(
        self, device_id: int, device_data: DeviceUpdate
    ) -> Optional[Device]:
        update_data = device_data.dict(exclude_unset=True)
        if not update_data:
            return await self.get_device(device_id)

        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.db.execute(
            update(Device)
            .where(Device.id == device_id)
            .values(**update_data)
            .returning(Device)
        )
        await self.db.commit()
        
        return result.scalar_one_or_none()

    async def delete_device(self, device_id: int) -> bool:
        result = await self.db.execute(
            delete(Device).where(Device.id == device_id)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def update_device_status(self, device_id: int, status: str) -> bool:
        result = await self.db.execute(
            update(Device)
            .where(Device.id == device_id)
            .values(
                status=status,
                last_seen=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        await self.db.commit()
        return result.rowcount > 0
