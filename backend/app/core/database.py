"""Database configuration and session management."""
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool
import structlog

from app.core.config import settings

logger = structlog.get_logger()


# Create declarative base for models
Base = declarative_base()


def create_engine() -> AsyncEngine:
    """Create async database engine with optimized settings."""
    db_url = str(settings.DATABASE_URL).lower()
    is_sqlite = "sqlite" in db_url
    
    # Base engine arguments
    engine_args = {
        "echo": settings.DATABASE_ECHO,
        "future": True,
        "echo_pool": settings.DEBUG,
    }
    
    # Add pool configuration only for non-SQLite databases
    if not is_sqlite:
        engine_args.update({
            "pool_class": QueuePool,
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_pre_ping": True,  # Test connections before using them
            "pool_recycle": 3600,   # Recycle connections after 1 hour
        })
    # SQLite doesn't need explicit pool configuration
    
    engine = create_async_engine(str(settings.DATABASE_URL), **engine_args)
    return engine


# Create engine instance
engine: AsyncEngine = create_engine()


# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


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

