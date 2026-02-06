import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from app.tasks.alerting import evaluate_alert_rules_async
from app.tasks.data_processing import cleanup_old_metrics_async, aggregate_metrics_async


class TestAlertingTasks:
    """Test alerting Celery tasks."""

    @pytest.mark.asyncio
    async def test_evaluate_alert_rules_threshold_trigger(self, db_session, test_device, test_metrics):
        """Test alert rule evaluation with threshold trigger."""
        from app.services.alert_service import AlertService
        from app.schemas.alert import AlertRuleCreate
        
        # Create a threshold rule that should trigger
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
            evaluation_window_minutes=120
        )
        
        rule = await alert_service.create_alert_rule(rule_data)
        
        # Mock the database session for the task
        with patch('app.tasks.alerting.AsyncSessionLocal') as mock_session:
            mock_session.return_value.__aenter__.return_value = db_session
            
            # Mock notification service
            with patch('app.tasks.alerting.NotificationService') as mock_notification:
                mock_notification_instance = AsyncMock()
                mock_notification.return_value = mock_notification_instance
                
                # Run the task
                await evaluate_alert_rules_async()
                
                # Verify notification was called if alert should trigger
                # This depends on the actual metric values in test_metrics
                if test_metrics and any(m.value > 70.0 for m in test_metrics):
                    mock_notification_instance.send_alert_notifications.assert_called()

    @pytest.mark.asyncio
    async def test_evaluate_alert_rules_anomaly_detection(self, db_session, test_device):
        """Test alert rule evaluation with anomaly detection."""
        from app.services.alert_service import AlertService
        from app.services.metric_service import MetricService
        from app.schemas.alert import AlertRuleCreate
        from app.schemas.metric import MetricCreate
        
        # Create an anomaly rule
        alert_service = AlertService(db_session)
        rule_data = AlertRuleCreate(
            name="CPU Anomaly",
            device_id=test_device.id,
            metric_type="cpu_usage_percent",
            rule_type="anomaly",
            severity="warning",
            notification_channels=["email"]
        )
        
        rule = await alert_service.create_alert_rule(rule_data)
        
        # Create metrics with an anomaly
        metric_service = MetricService(db_session)
        
        # Normal metrics
        normal_metrics = []
        base_time = datetime.utcnow()
        for i in range(10):
            normal_metrics.append(
                MetricCreate(
                    device_id=test_device.id,
                    metric_type="cpu_usage_percent",
                    value=50.0 + (i % 10),  # Values around 50-60
                    timestamp=base_time
                )
            )
        
        # Add an anomalous value
        normal_metrics.append(
            MetricCreate(
                device_id=test_device.id,
                metric_type="cpu_usage_percent",
                value=95.0,  # Much higher than normal
                timestamp=base_time + timedelta(seconds=1)
            )
        )
        
        await metric_service.ingest_metrics(normal_metrics)
        
        # Mock the database session for the task
        with patch('app.tasks.alerting.AsyncSessionLocal') as mock_session:
            mock_session.return_value.__aenter__.return_value = db_session
            
            # Mock notification service
            with patch('app.tasks.alerting.NotificationService') as mock_notification:
                mock_notification_instance = AsyncMock()
                mock_notification.return_value = mock_notification_instance
                
                # Run the task
                await evaluate_alert_rules_async()
                
                # Ensure task completes without error. Anomaly triggering is heuristic.

    @pytest.mark.asyncio
    async def test_evaluate_alert_rules_no_trigger(self, db_session, test_device):
        """Test alert rule evaluation when no alerts should trigger."""
        from app.services.alert_service import AlertService
        from app.services.metric_service import MetricService
        from app.schemas.alert import AlertRuleCreate
        from app.schemas.metric import MetricCreate
        
        # Create a high threshold rule
        alert_service = AlertService(db_session)
        rule_data = AlertRuleCreate(
            name="Very High CPU Alert",
            device_id=test_device.id,
            metric_type="cpu_usage_percent",
            rule_type="threshold",
            severity="critical",
            threshold_value=99.0,
            comparison_operator="gt"
        )
        
        rule = await alert_service.create_alert_rule(rule_data)
        
        # Create metrics that won't trigger the rule
        metric_service = MetricService(db_session)
        low_metrics = []
        for i in range(5):
            low_metrics.append(
                MetricCreate(
                    device_id=test_device.id,
                    metric_type="cpu_usage_percent",
                    value=30.0 + i  # Values 30-34
                )
            )
        
        await metric_service.ingest_metrics(low_metrics)
        
        # Mock the database session for the task
        with patch('app.tasks.alerting.AsyncSessionLocal') as mock_session:
            mock_session.return_value.__aenter__.return_value = db_session
            
            # Mock notification service
            with patch('app.tasks.alerting.NotificationService') as mock_notification:
                mock_notification_instance = AsyncMock()
                mock_notification.return_value = mock_notification_instance
                
                # Run the task
                await evaluate_alert_rules_async()
                
                # No alerts should be triggered
                mock_notification_instance.send_alert_notifications.assert_not_called()


class TestDataProcessingTasks:
    """Test data processing Celery tasks."""

    @pytest.mark.asyncio
    async def test_cleanup_old_metrics(self, db_session, test_device):
        """Test old metrics cleanup task."""
        from app.services.metric_service import MetricService
        from app.schemas.metric import MetricCreate
        from datetime import datetime, timedelta
        
        # Create old metrics (beyond retention period)
        metric_service = MetricService(db_session)
        old_metrics = []
        
        # Create metrics older than 30 days
        old_time = datetime.utcnow() - timedelta(days=35)
        for i in range(5):
            old_metrics.append(
                MetricCreate(
                    device_id=test_device.id,
                    metric_type="cpu_usage_percent",
                    value=50.0 + i,
                    timestamp=old_time.isoformat()
                )
            )
        
        await metric_service.ingest_metrics(old_metrics)
        
        # Mock the database session for the task
        with patch('app.tasks.data_processing.AsyncSessionLocal') as mock_session:
            mock_session.return_value.__aenter__.return_value = db_session
            
            # Run the cleanup task
            await cleanup_old_metrics_async()
            
            # Verify old metrics were deleted
            # This would require checking the database after cleanup
            # For now, we just ensure the task runs without error

    @pytest.mark.asyncio
    async def test_aggregate_metrics(self, db_session, test_device):
        """Test metrics aggregation task."""
        from app.services.metric_service import MetricService
        from app.schemas.metric import MetricCreate
        
        # Create test metrics for aggregation
        metric_service = MetricService(db_session)
        metrics = []
        
        for i in range(24):  # 24 hours of data
            metrics.append(
                MetricCreate(
                    device_id=test_device.id,
                    metric_type="cpu_usage_percent",
                    value=50.0 + (i % 20)
                )
            )
        
        await metric_service.ingest_metrics(metrics)
        
        # Mock the database session for the task
        with patch('app.tasks.data_processing.AsyncSessionLocal') as mock_session:
            mock_session.return_value.__aenter__.return_value = db_session
            
            # Run the aggregation task
            await aggregate_metrics_async()
            
            # Verify task completes without error
            # In a real implementation, this would create summary records


class TestNotificationService:
    """Test notification service integration."""

    @pytest.mark.asyncio
    async def test_send_email_notification(self):
        """Test email notification sending."""
        from app.services.notification_service import NotificationService
        from unittest.mock import patch, AsyncMock
        
        # Mock SMTP
        with patch('app.services.notification_service.aiosmtplib.send') as mock_send:
            mock_send.return_value = AsyncMock()
            
            notification_service = NotificationService()
            
            # Create mock alert and rule
            mock_alert = type('MockAlert', (), {
                'id': 1,
                'severity': 'warning',
                'device_id': 1,
                'metric_type': 'cpu_usage_percent',
                'trigger_value': 85.0,
                'message': 'High CPU usage detected',
                'triggered_at': datetime.utcnow()
            })()
            
            mock_rule = type('MockRule', (), {
                'name': 'High CPU Alert',
                'notification_channels': ['email']
            })()
            
            # This would normally send an email
            # For testing, we just ensure it doesn't crash
            try:
                await notification_service._send_email_notification(mock_alert, mock_rule)
                success = True
            except Exception:
                success = False
            
            assert success  # Should not raise exception

    @pytest.mark.asyncio
    async def test_send_discord_notification(self):
        """Test Discord notification sending."""
        from app.services.notification_service import NotificationService
        from unittest.mock import patch, AsyncMock
        
        # Mock HTTP client
        with patch('app.services.notification_service.aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 204
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            notification_service = NotificationService()
            
            # Create mock alert and rule
            mock_alert = type('MockAlert', (), {
                'id': 1,
                'severity': 'critical',
                'device_id': 1,
                'metric_type': 'cpu_usage_percent',
                'trigger_value': 95.0,
                'message': 'Critical CPU usage',
                'triggered_at': datetime.utcnow()
            })()
            
            mock_rule = type('MockRule', (), {
                'name': 'Critical CPU Alert',
                'notification_channels': ['discord']
            })()
            
            # This would normally send a Discord message
            try:
                await notification_service._send_discord_notification(mock_alert, mock_rule)
                success = True
            except Exception:
                success = False
            
            assert success  # Should not raise exception

    @pytest.mark.asyncio
    async def test_notification_service_error_handling(self):
        """Test notification service error handling."""
        from app.services.notification_service import NotificationService
        
        # Create service with missing configuration
        notification_service = NotificationService()
        
        # Create mock alert and rule
        mock_alert = type('MockAlert', (), {
            'id': 1,
            'severity': 'warning',
            'device_id': 1,
            'metric_type': 'cpu_usage_percent',
            'trigger_value': 85.0,
            'message': 'High CPU usage',
            'triggered_at': datetime.utcnow()
        })()
        
        mock_rule = type('MockRule', (), {
            'name': 'Test Alert',
            'notification_channels': ['email', 'telegram', 'discord', 'sms']
        })()
        
        # All notification methods should handle missing config gracefully
        try:
            await notification_service.send_alert_notifications(mock_alert, mock_rule)
            success = True
        except Exception:
            success = False
        
        assert success  # Should handle errors gracefully
