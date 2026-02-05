from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router
from app.core.logging import setup_logging

setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting HomeGuard Monitor backend")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    logger.info("Shutting down HomeGuard Monitor backend")


app = FastAPI(
    title="HomeGuard Monitor API",
    description="A comprehensive monitoring and alerting system for personal servers and IoT devices",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "homeguard-monitor"}


@app.get("/")
async def root():
    return {
        "message": "HomeGuard Monitor API",
        "version": "1.0.0",
        "docs": "/docs"
    }
