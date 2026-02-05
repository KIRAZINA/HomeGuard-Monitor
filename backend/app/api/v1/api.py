from fastapi import APIRouter
from app.api.v1.endpoints import devices, metrics, alerts, auth

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
