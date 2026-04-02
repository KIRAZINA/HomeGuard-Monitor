"""Custom exception definitions for the application."""
from typing import Any, Dict, Optional


class HomeGuardException(Exception):
    """Base exception for HomeGuard Monitor."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize exception.
        
        Args:
            message: Human-readable error message
            status_code: HTTP status code
            error_code: Machine-readable error code
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(HomeGuardException):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class NotFoundError(HomeGuardException):
    """Raised when a resource is not found."""
    
    def __init__(self, resource: str, **kwargs: Any) -> None:
        super().__init__(
            message=f"{resource} not found",
            status_code=404,
            error_code="NOT_FOUND",
            **kwargs,
        )


class DuplicateError(HomeGuardException):
    """Raised when attempting to create a duplicate resource."""
    
    def __init__(self, resource: str, **kwargs: Any) -> None:
        super().__init__(
            message=f"{resource} already exists",
            status_code=409,
            error_code="DUPLICATE_RESOURCE",
            **kwargs,
        )


class AuthenticationError(HomeGuardException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Invalid credentials") -> None:
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
        )


class AuthorizationError(HomeGuardException):
    """Raised when user lacks required permissions."""
    
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
        )


class DatabaseError(HomeGuardException):
    """Raised when database operation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code="DATABASE_ERROR",
            details=details,
        )


class ExternalServiceError(HomeGuardException):
    """Raised when external service fails."""
    
    def __init__(self, service: str, message: str) -> None:
        super().__init__(
            message=f"{service} service error: {message}",
            status_code=503,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service},
        )


class ConfigurationError(HomeGuardException):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str) -> None:
        super().__init__(
            message=f"Configuration error: {message}",
            status_code=500,
            error_code="CONFIGURATION_ERROR",
        )


class TaskError(HomeGuardException):
    """Raised when background task fails."""
    
    def __init__(self, task_name: str, message: str) -> None:
        super().__init__(
            message=f"Task '{task_name}' failed: {message}",
            status_code=500,
            error_code="TASK_ERROR",
            details={"task": task_name},
        )
