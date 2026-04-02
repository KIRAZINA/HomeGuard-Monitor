"""API v1 router configuration."""
from fastapi import APIRouter
from app.api.v1.endpoints import devices, metrics, alerts, auth

# Create main API router
api_router = APIRouter()

# Include endpoint routers with proper prefix and tags
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"],
)
api_router.include_router(
    devices.router,
    prefix="/devices",
)
api_router.include_router(
    metrics.router,
    prefix="/metrics",
)
api_router.include_router(
    alerts.router,
    prefix="/alerts",
)

