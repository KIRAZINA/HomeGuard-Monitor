"""Logging configuration."""
import structlog
import logging
import sys
from app.core.config import settings


def setup_logging() -> None:
    """Configure structured logging with structlog."""
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            # Filter by level
            structlog.stdlib.filter_by_level,
            # Add logger name
            structlog.stdlib.add_logger_name,
            # Add log level
            structlog.stdlib.add_log_level,
            # Positional arguments formatter
            structlog.stdlib.PositionalArgumentsFormatter(),
            # Add timestamp in ISO format
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            # Include stack info for exceptions
            structlog.processors.StackInfoRenderer(),
            # Format exception info
            structlog.processors.format_exc_info,
            # Decode unicode
            structlog.processors.UnicodeDecoder(),
            # JSON renderer for production, console for development
            (
                structlog.processors.JSONRenderer()
                if settings.ENVIRONMENT == "production"
                else structlog.dev.ConsoleRenderer()
            ),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger() -> structlog.BoundLogger:
    """Get configured logger instance.
    
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger()

