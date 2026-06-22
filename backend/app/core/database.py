"""Database configuration and session management."""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
import structlog

from app.core.config import settings

logger = structlog.get_logger()


# Create declarative base for models
Base = declarative_base()


def create_async_db_engine() -> AsyncEngine:
    """Create async database engine with optimized settings."""
    db_url = str(settings.DATABASE_URL).lower()
    is_sqlite = "sqlite" in db_url
    
    base_args = {
        "echo": settings.DATABASE_ECHO,
        "future": True,
        "echo_pool": settings.DEBUG,
    }
    
    if not is_sqlite:
        base_args.update({
            "pool_class": QueuePool,
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        })
    
    engine = create_async_engine(str(settings.DATABASE_URL), **base_args)
    return engine


# Create engine instance
engine: AsyncEngine = create_async_db_engine()


# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# Synchronous engine for Celery workers
sync_db_url = str(settings.DATABASE_URL).replace("+asyncpg", "+psycopg2")
is_sync_sqlite = "sqlite" in sync_db_url.lower()
sync_engine_kwargs = {"pool_pre_ping": True}
if not is_sync_sqlite:
    sync_engine_kwargs.update(pool_size=5, max_overflow=5)
sync_engine = create_engine(sync_db_url, **sync_engine_kwargs)
SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)


def get_sync_db():
    """Get synchronous database session for Celery tasks.

    Yields:
        SQLAlchemy Session
    """
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_db() -> AsyncSession:
    """Get database session dependency.
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.exception("database_error", exc_info=e)
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_initialized")


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
    logger.info("database_connections_closed")

