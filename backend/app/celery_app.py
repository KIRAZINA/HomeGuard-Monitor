"""Celery application configuration."""
from celery import Celery
from celery.schedules import schedule
from app.core.config import settings
import structlog

logger = structlog.get_logger()

# Create Celery app instance
celery_app = Celery(
    "homeguard_monitor",
    broker=str(settings.CELERY_BROKER_URL),
    backend=str(settings.CELERY_RESULT_BACKEND),
    include=[
        "app.tasks.alerting",
        "app.tasks.data_processing",
    ],
)

# Configure Celery
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
    task_time_limit=settings.CELERY_TASK_TIMEOUT,
    task_soft_time_limit=int(settings.CELERY_TASK_TIMEOUT * 0.9),
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Result backend settings
    result_expires=3600,
    result_backend_transport_options={
        "visibility_timeout": 3600,
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "evaluate-alert-rules": {
            "task": "app.tasks.alerting.evaluate_alert_rules",
            "schedule": settings.ALERT_EVALUATION_INTERVAL_SECONDS,
            "options": {
                "expires": settings.ALERT_EVALUATION_INTERVAL_SECONDS * 2,
            },
        },
        "cleanup-old-metrics": {
            "task": "app.tasks.data_processing.cleanup_old_metrics",
            "schedule": 3600.0,  # Run every hour
            "options": {
                "expires": 7200,  # Task expires after 2 hours
            },
        },
        "aggregate-metrics": {
            "task": "app.tasks.data_processing.aggregate_metrics",
            "schedule": 300.0,  # Run every 5 minutes
            "options": {
                "expires": 600,
            },
        },
    },
)


@celery_app.task(bind=True, max_retries=3)
def debug_task(self):
    """Debug task for testing."""
    try:
        logger.info("celery_debug_task_executed", retry_count=self.request.retries)
        return {"status": "ok"}
    except Exception as exc:
        # Exponential backoff: 2^x * 60 seconds
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

