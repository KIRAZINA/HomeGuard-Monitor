"""Error handling utilities."""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Callable, Union
import structlog

from app.core.exceptions import HomeGuardException

logger = structlog.get_logger()


class ErrorResponse:
    """Standardized error response."""
    
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: dict | None = None,
    ):
        """Initialize error response."""
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details if self.details else None,
            }
        }


async def exception_handler(
    request: Request,
    exc: HomeGuardException,
) -> JSONResponse:
    """Handle HomeGuard exceptions."""
    logger.warning(
        "application_error",
        path=request.url.path,
        method=request.method,
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
    )
    
    error_response = ErrorResponse(
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.to_dict(),
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    logger.warning(
        "http_error",
        path=request.url.path,
        method=request.method,
        status_code=exc.status_code,
        detail=exc.detail,
    )
    
    error_response = ErrorResponse(
        status_code=exc.status_code,
        error_code="HTTP_ERROR",
        message=str(exc.detail),
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.to_dict(),
    )


async def general_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unhandled exceptions."""
    logger.exception(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        exc_type=exc.__class__.__name__,
    )
    
    error_response = ErrorResponse(
        status_code=500,
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.to_dict(),
    )
