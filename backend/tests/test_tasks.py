import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from app.tasks.alerting import evaluate_alert_rules
from app.tasks.data_processing import cleanup_old_metrics, aggregate_metrics


class TestAlertingTasks:
    """Test alerting Celery tasks."""

    @pytest.mark.asyncio
    async def test_evaluate_alert_rules_threshold_trigger(
        self, db_session, test_device, test_metrics
    ):
        """Test alert rule evaluation with threshold trigger."""
        from app.services.alert_service import AlertService
        from app.schemas.alert import AlertRuleCreate

        alert_service = AlertService(db_session)
        rule_data = AlertRuleCreate(
            name="High CPU Alert",
            device_id=test_device.id,
            metric_type="cpu_usage_percent",
            rule_type="threshold",
            severity="warning",
            threshold_value=70.0,
            comparison_operator="gt",
            notification_channels=["email"],
            evaluation_window_minutes=120,
        )

        rule = await alert_service.create_alert_rule(rule_data)

        with patch("app.tasks.alerting.SyncSessionLocal") as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            evaluate_alert_rules()

    @pytest.mark.asyncio
    async def test_evaluate_alert_rules_anomaly_detection(self, db_session, test_device):
        """Test alert rule evaluation with anomaly detection."""
        from app.services.alert_service import AlertService
        from app.services.metric_service import MetricService
        from app.schemas.alert import AlertRuleCreate
        from app.schemas.metric import MetricCreate

        alert_service = AlertService(db_session)
        rule_data = AlertRuleCreate(
            name="CPU Anomaly",
            device_id=test_device.id,
            metric_type="cpu_usage_percent",
            rule_type="anomaly",
            severity="warning",
            notification_channels=["email"],
        )

        rule = await alert_service.create_alert_rule(rule_data)

        metric_service = MetricService(db_session)
        normal_metrics = []
        base_time = datetime.utcnow()
        for i in range(10):
            normal_metrics.append(
                MetricCreate(
                    device_id=test_device.id,
                    metric_type="cpu_usage_percent",
                    value=50.0 + (i % 10),
                    timestamp=base_time,
                )
            )
        normal_metrics.append(
            MetricCreate(
                device_id=test_device.id,
                metric_type="cpu_usage_percent",
                value=95.0,
                timestamp=base_time + timedelta(seconds=1),
            )
        )
        await metric_service.ingest_metrics(normal_metrics)

        with patch("app.tasks.alerting.SyncSessionLocal") as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            evaluate_alert_rules()

    @pytest.mark.asyncio
    async def test_evaluate_alert_rules_no_trigger(self, db_session, test_device):
        """Test alert rule evaluation when no alerts should trigger."""
        from app.services.alert_service import AlertService
        from app.services.metric_service import MetricService
        from app.schemas.alert import AlertRuleCreate
        from app.schemas.metric import MetricCreate

        alert_service = AlertService(db_session)
        rule_data = AlertRuleCreate(
            name="Very High CPU Alert",
            device_id=test_device.id,
            metric_type="cpu_usage_percent",
            rule_type="threshold",
            severity="critical",
            threshold_value=99.0,
            comparison_operator="gt",
        )

        rule = await alert_service.create_alert_rule(rule_data)

        metric_service = MetricService(db_session)
        low_metrics = []
        for i in range(5):
            low_metrics.append(
                MetricCreate(
                    device_id=test_device.id, metric_type="cpu_usage_percent", value=30.0 + i
                )
            )
        await metric_service.ingest_metrics(low_metrics)

        with patch("app.tasks.alerting.SyncSessionLocal") as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            evaluate_alert_rules()


class TestDataProcessingTasks:
    """Test data processing Celery tasks."""

    @pytest.mark.asyncio
    async def test_cleanup_old_metrics(self, db_session, test_device):
        """Test old metrics cleanup task."""
        from app.services.metric_service import MetricService
        from app.schemas.metric import MetricCreate

        metric_service = MetricService(db_session)
        old_time = datetime.utcnow() - timedelta(days=35)
        old_metrics = [
            MetricCreate(
                device_id=test_device.id,
                metric_type="cpu_usage_percent",
                value=50.0 + i,
                timestamp=old_time.isoformat(),
            )
            for i in range(5)
        ]
        await metric_service.ingest_metrics(old_metrics)

        with patch("app.tasks.data_processing.SyncSessionLocal") as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            cleanup_old_metrics()

    @pytest.mark.asyncio
    async def test_aggregate_metrics(self, db_session, test_device):
        """Test metrics aggregation task."""
        from app.services.metric_service import MetricService
        from app.schemas.metric import MetricCreate

        metric_service = MetricService(db_session)
        metrics = [
            MetricCreate(
                device_id=test_device.id, metric_type="cpu_usage_percent", value=50.0 + (i % 20)
            )
            for i in range(24)
        ]
        await metric_service.ingest_metrics(metrics)

        with patch("app.tasks.data_processing.SyncSessionLocal") as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            aggregate_metrics()


class TestNotificationService:
    """Test notification service integration."""

    @pytest.mark.asyncio
    async def test_send_email_notification(self):
        """Test email notification sending."""
        from app.services.notification_service import NotificationService
        from unittest.mock import patch, AsyncMock

        with patch("app.services.notification_service.aiosmtplib.send") as mock_send:
            mock_send.return_value = AsyncMock()

            notification_service = NotificationService()

            mock_alert = type(
                "MockAlert",
                (),
                {
                    "id": 1,
                    "severity": "warning",
                    "device_id": 1,
                    "metric_type": "cpu_usage_percent",
                    "trigger_value": 85.0,
                    "message": "High CPU usage detected",
                    "triggered_at": datetime.utcnow(),
                },
            )()

            mock_rule = type(
                "MockRule", (), {"name": "High CPU Alert", "notification_channels": ["email"]}
            )()

            try:
                await notification_service._send_email_notification(mock_alert, mock_rule)
                success = True
            except Exception:
                success = False

            assert success

    @pytest.mark.asyncio
    async def test_send_discord_notification(self):
        """Test Discord notification sending."""
        from app.services.notification_service import NotificationService
        from unittest.mock import patch, AsyncMock

        with patch("app.services.notification_service.aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 204
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = (
                mock_response
            )

            notification_service = NotificationService()

            mock_alert = type(
                "MockAlert",
                (),
                {
                    "id": 1,
                    "severity": "critical",
                    "device_id": 1,
                    "metric_type": "cpu_usage_percent",
                    "trigger_value": 95.0,
                    "message": "Critical CPU usage",
                    "triggered_at": datetime.utcnow(),
                },
            )()

            mock_rule = type(
                "MockRule", (), {"name": "Critical CPU Alert", "notification_channels": ["discord"]}
            )()

            try:
                await notification_service._send_discord_notification(mock_alert, mock_rule)
                success = True
            except Exception:
                success = False

            assert success

    @pytest.mark.asyncio
    async def test_notification_service_error_handling(self):
        """Test notification service error handling."""
        from app.services.notification_service import NotificationService

        notification_service = NotificationService()

        mock_alert = type(
            "MockAlert",
            (),
            {
                "id": 1,
                "severity": "warning",
                "device_id": 1,
                "metric_type": "cpu_usage_percent",
                "trigger_value": 85.0,
                "message": "High CPU usage",
                "triggered_at": datetime.utcnow(),
            },
        )()

        mock_rule = type(
            "MockRule",
            (),
            {
                "name": "Test Alert",
                "notification_channels": ["email", "telegram", "discord", "sms"],
            },
        )()

        try:
            await notification_service.send_alert_notifications(mock_alert, mock_rule)
            success = True
        except Exception:
            success = False

        assert success
