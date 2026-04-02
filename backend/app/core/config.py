"""Application configuration with environment validation."""
from pydantic import Field, HttpUrl, RedisDsn, validator, AnyUrl
from pydantic_settings import BaseSettings
from typing import List, Optional
from enum import Enum


class EnvironmentEnum(str, Enum):
    """Supported environments."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # Application
    PROJECT_NAME: str = "HomeGuard Monitor"
    VERSION: str = "1.0.0"
    ENVIRONMENT: EnvironmentEnum = Field(
        default=EnvironmentEnum.DEVELOPMENT,
        description="Application environment"
    )
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode (never in production)"
    )
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost/homeguard",
        description="PostgreSQL database URL (or SQLite for testing)"
    )
    DATABASE_ECHO: bool = Field(
        default=False,
        description="Enable SQL query logging"
    )
    DATABASE_POOL_SIZE: int = Field(
        default=20,
        description="Database connection pool size"
    )
    DATABASE_MAX_OVERFLOW: int = Field(
        default=10,
        description="Maximum overflow connections"
    )
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis cache URL"
    )
    
    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT secret key (must be changed in production)",
        min_length=32
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=1,
        description="JWT token expiration in minutes"
    )
    
    # CORS
    ALLOWED_HOSTS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed origins for CORS"
    )
    
    # Celery
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend URL"
    )
    CELERY_TASK_TIMEOUT: int = Field(
        default=300,
        ge=10,
        description="Task timeout in seconds"
    )
    
    # Notification settings
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(
        default=None,
        description="Telegram bot token"
    )
    DISCORD_WEBHOOK_URL: Optional[str] = Field(
        default=None,
        description="Discord webhook URL"
    )
    TWILIO_ACCOUNT_SID: Optional[str] = Field(
        default=None,
        description="Twilio account SID"
    )
    TWILIO_AUTH_TOKEN: Optional[str] = Field(
        default=None,
        description="Twilio auth token"
    )
    SMTP_HOST: Optional[str] = Field(
        default=None,
        description="SMTP server host"
    )
    SMTP_PORT: int = Field(
        default=587,
        ge=1,
        le=65535,
        description="SMTP server port"
    )
    SMTP_USERNAME: Optional[str] = Field(
        default=None,
        description="SMTP username"
    )
    SMTP_PASSWORD: Optional[str] = Field(
        default=None,
        description="SMTP password"
    )
    SMTP_FROM_EMAIL: Optional[str] = Field(
        default=None,
        description="Sender email address"
    )
    
    # Monitoring
    METRICS_RETENTION_DAYS: int = Field(
        default=30,
        ge=1,
        description="Metrics retention period in days"
    )
    ALERT_EVALUATION_INTERVAL_SECONDS: int = Field(
        default=60,
        ge=10,
        description="Alert evaluation interval in seconds"
    )
    ALERT_COOLDOWN_SECONDS: int = Field(
        default=300,
        ge=10,
        description="Alert cooldown period in seconds"
    )
    
    # Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        json_schema_extra = {
            "example": {
                "PROJECT_NAME": "HomeGuard Monitor",
                "ENVIRONMENT": "development",
                "SECRET_KEY": "your-secret-key-minimum-32-characters-long"
            }
        }
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v: str) -> str:
        """Validate environment setting."""
        return v.lower()


# Global settings instance
settings = Settings()
