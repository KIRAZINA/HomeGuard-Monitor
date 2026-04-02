"""FastAPI application factory."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import structlog

from app.core.config import settings, EnvironmentEnum
from app.core.database import engine, Base, init_db, close_db
from app.core.logging import setup_logging
from app.core.exceptions import HomeGuardException
from app.core.errors import exception_handler, http_exception_handler, general_exception_handler
from app.api.v1.api import api_router

# Setup logging
setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info(
        "application_startup",
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )
    
    try:
        await init_db()
        logger.info("database_ready")
    except Exception as e:
        logger.exception("database_initialization_failed", exc=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("application_shutdown")
    try:
        await close_db()
    except Exception as e:
        logger.exception("database_cleanup_failed", exc=str(e))


def create_app() -> FastAPI:
    """Create FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="A comprehensive monitoring and alerting system for personal servers and IoT devices",
        version=settings.VERSION,
        lifespan=lifespan,
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
    )
    
    # Add exception handlers
    app.add_exception_handler(HomeGuardException, exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    # Add middleware stack (order matters - last added is first executed)
    
    # Trusted host middleware for production
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS,
        )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        max_age=3600,
    )
    
    # Include routers
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Health check endpoints
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "homeguard-monitor",
            "version": settings.VERSION,
        }
    
    @app.get("/health/ready", tags=["Health"])
    async def readiness_check() -> dict[str, str]:
        """Readiness check endpoint."""
        return {
            "status": "ready",
            "service": "homeguard-monitor",
        }
    
    @app.get("/", tags=["Info"])
    async def root() -> dict[str, str]:
        """Root endpoint."""
        return {
            "message": f"{settings.PROJECT_NAME} API",
            "version": settings.VERSION,
            "docs": "/docs" if settings.ENVIRONMENT != "production" else "Not available",
        }
    
    return app


# Create app instance
app = create_app()

