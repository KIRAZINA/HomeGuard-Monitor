"""Device API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import structlog

from app.core.database import get_db
from app.schemas.device import DeviceCreate, DeviceResponse, DeviceUpdate
from app.services.device_service import DeviceService
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError

logger = structlog.get_logger()

router = APIRouter(tags=["Devices"])


@router.post(
    "/",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create device",
    responses={
        409: {"description": "Device with this hostname already exists"},
        422: {"description": "Invalid input data"},
    },
)
async def create_device(
    device: DeviceCreate,
    db: AsyncSession = Depends(get_db),
) -> DeviceResponse:
    """Create a new device.
    
    Args:
        device: Device creation data
        db: Database session
        
    Returns:
        Created device
    """
    try:
        device_service = DeviceService(db)
        created_device = await device_service.create_device(device)
        logger.info("device_creation_request", device_name=device.name)
        return created_device
    except DuplicateError as e:
        logger.warning("duplicate_device", hostname=device.hostname)
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        ) from e
    except DatabaseError as e:
        logger.exception("device_creation_failed")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        ) from e


@router.get(
    "/",
    response_model=List[DeviceResponse],
    summary="List devices",
    responses={
        200: {"description": "List of devices"},
    },
)
async def list_devices(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    status: str | None = Query(None, description="Filter by device status"),
    device_type: str | None = Query(None, description="Filter by device type"),
    db: AsyncSession = Depends(get_db),
) -> List[DeviceResponse]:
    """Get paginated devices list.
    
    Args:
        skip: Number of records to skip
        limit: Maximum records to return
        status: Optional status filter
        device_type: Optional device type filter
        db: Database session
        
    Returns:
        List of devices
    """
    try:
        device_service = DeviceService(db)
        devices = await device_service.get_devices(
            skip=skip,
            limit=limit,
            status=status,
            device_type=device_type,
        )
        logger.info(
            "list_devices_request",
            skip=skip,
            limit=limit,
            count=len(devices),
        )
        return devices
    except DatabaseError as e:
        logger.exception("list_devices_failed")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        ) from e


@router.get(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Get device",
    responses={
        200: {"description": "Device details"},
        404: {"description": "Device not found"},
    },
)
async def get_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
) -> DeviceResponse:
    """Get device by ID.
    
    Args:
        device_id: Device ID
        db: Database session
        
    Returns:
        Device details
    """
    try:
        device_service = DeviceService(db)
        device = await device_service.get_device(device_id)
        if not device:
            logger.warning("device_not_found", device_id=device_id)
            raise NotFoundError("Device")
        
        logger.info("get_device_request", device_id=device_id)
        return device
    except NotFoundError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        ) from e
    except DatabaseError as e:
        logger.exception("get_device_failed", device_id=device_id)
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        ) from e


@router.put(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Update device",
    responses={
        200: {"description": "Updated device"},
        404: {"description": "Device not found"},
        409: {"description": "Hostname already taken"},
    },
)
async def update_device(
    device_id: int,
    device_update: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
) -> DeviceResponse:
    """Update a device.
    
    Args:
        device_id: Device ID
        device_update: Device update data
        db: Database session
        
    Returns:
        Updated device
    """
    try:
        device_service = DeviceService(db)
        device = await device_service.update_device(device_id, device_update)
        
        if not device:
            logger.warning("device_not_found_update", device_id=device_id)
            raise NotFoundError("Device")
        
        logger.info("device_update_request", device_id=device_id)
        return device
    except (NotFoundError, DuplicateError) as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        ) from e
    except DatabaseError as e:
        logger.exception("update_device_failed", device_id=device_id)
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        ) from e


@router.delete(
    "/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete device",
    responses={
        204: {"description": "Device deleted"},
        404: {"description": "Device not found"},
    },
)
async def delete_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a device.
    
    Args:
        device_id: Device ID to delete
        db: Database session
    """
    try:
        device_service = DeviceService(db)
        success = await device_service.delete_device(device_id)
        
        if not success:
            logger.warning("device_not_found_delete", device_id=device_id)
            raise NotFoundError("Device")
        
        logger.info("device_delete_request", device_id=device_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        ) from e
    except DatabaseError as e:
        logger.exception("delete_device_failed", device_id=device_id)
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        ) from e

