from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "homeguard_monitor",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.alerting", "app.tasks.data_processing"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "evaluate-alert-rules": {
            "task": "app.tasks.alerting.evaluate_alert_rules",
            "schedule": settings.ALERT_EVALUATION_INTERVAL_SECONDS,
        },
        "cleanup-old-metrics": {
            "task": "app.tasks.data_processing.cleanup_old_metrics",
            "schedule": 3600.0,  # Run every hour
        },
    },
)
