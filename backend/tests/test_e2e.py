"""
End-to-end tests for HomeGuard Monitor.
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


class TestE2EDeviceMonitoring:
    """End-to-end tests for device monitoring workflow."""
    
    @pytest.mark.e2e
    async def test_complete_device_monitoring_workflow(self, client: AsyncClient, auth_headers, db_session):
        """
        Test complete device monitoring workflow:
        1. Register device
        2. Ingest metrics
        3. Verify metrics stored
        4. Create alert rule
        5. Trigger alert
        6. Verify notification
        """
        from app.services.device_service import DeviceService
        from app.services.metric_service import MetricService
        from app.services.alert_service import AlertService
        from app.schemas.device import DeviceCreate
        from app.schemas.metric import MetricCreate
        from app.schemas.alert import AlertRuleCreate
        
        # 1. Register a new device
        device_service = DeviceService(db_session)
        device_data = DeviceCreate(
            name="E2E Test Server",
            description="Server for E2E testing",
            device_type="server",
            hostname="e2e-test.local",
            ip_address="192.168.1.200"
        )
        device = await device_service.create_device(device_data)
        device_id = device.id
        
        assert device_id is not None
        assert device.name == "E2E Test Server"
        
        # 2. Ingest metrics
        metric_service = MetricService(db_session)
        metrics_data = [
            MetricCreate(
                device_id=device_id,
                metric_type="cpu_usage_percent",
                value=75.0,
                unit="percent"
            ),
            MetricCreate(
                device_id=device_id,
                metric_type="memory_usage_percent",
                value=60.0,
                unit="percent"
            ),
            MetricCreate(
                device_id=device_id,
                metric_type="disk_usage_percent",
                value=45.0,
                unit="percent"
            )
        ]
        await metric_service.ingest_metrics(metrics_data)
        
        # 3. Verify metrics stored
        query_result = await metric_service.get_metrics(
            device_id=device_id,
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow()
        )
        
        assert len(query_result) >= 3
        
        # 4. Create alert rule
        alert_service = AlertService(db_session)
        rule_data = AlertRuleCreate(
            name="E2E CPU Alert",
            device_id=device_id,
            metric_type="cpu_usage_percent",
            rule_type="threshold",
            severity="warning",
            threshold_value=70.0,
            comparison_operator="gt",
            notification_channels=["email"]
        )
        rule = await alert_service.create_alert_rule(rule_data)
        
        assert rule.id is not None
        assert rule.threshold_value == 70.0
        
        # 5. Trigger alert by ingesting high CPU
        high_cpu_metric = MetricCreate(
            device_id=device_id,
            metric_type="cpu_usage_percent",
            value=85.0,  # Above threshold
            unit="percent"
        )
        await metric_service.ingest_metrics([high_cpu_metric])
        
        # 6. Verify alert was created
        alerts = await alert_service.get_alerts()
        cpu_alerts = [a for a in alerts if a.metric_type == "cpu_usage_percent"]
        
        assert len(cpu_alerts) >= 1


class TestE2EAlertWorkflow:
    """End-to-end tests for alert workflow."""
    
    @pytest.mark.e2e
    async def test_alert_acknowledge_workflow(self, client: AsyncClient, auth_headers, db_session):
        """
        Test alert acknowledge workflow:
        1. Create device and alert rule
        2. Trigger alert
        3. Acknowledge alert
        4. Verify alert status
        """
        from app.services.device_service import DeviceService
        from app.services.alert_service import AlertService
        from app.schemas.device import DeviceCreate
        from app.schemas.alert import AlertRuleCreate, AlertCreate
        
        # Create device
        device_service = DeviceService(db_session)
        device = await device_service.create_device(
            DeviceCreate(
                name="Alert Test Device",
                device_type="server",
                hostname="alert-test.local"
            )
        )
        
        # Create alert rule
        alert_service = AlertService(db_session)
        rule = await alert_service.create_alert_rule(
            AlertRuleCreate(
                name="Test Alert Rule",
                device_id=device.id,
                metric_type="cpu_usage_percent",
                rule_type="threshold",
                severity="warning",
                threshold_value=80.0,
                comparison_operator="gt"
            )
        )
        
        # Manually create an alert for testing
        alert = await alert_service.create_alert(
            AlertCreate(
                rule_id=rule.id,
                device_id=device.id,
                metric_type="cpu_usage_percent",
                severity="warning",
                message="Test alert message",
                trigger_value=85.0
            )
        )
        
        assert alert.status == "active"
        
        # Acknowledge alert
        success = await alert_service.acknowledge_alert(alert.id, "test_user")
        
        assert success is True
        
        # Verify alert status
        alerts = await alert_service.get_alerts()
        acknowledged = next((a for a in alerts if a.id == alert.id), None)
        
        assert acknowledged is not None
        assert acknowledged.status == "acknowledged"
        assert acknowledged.acknowledged_by == "test_user"

    @pytest.mark.e2e
    async def test_alert_snooze_workflow(self, client: AsyncClient, auth_headers, db_session):
        """
        Test alert snooze workflow:
        1. Create alert
        2. Snooze alert
        3. Verify snooze status
        """
        from app.services.device_service import DeviceService
        from app.services.alert_service import AlertService
        from app.schemas.device import DeviceCreate
        from app.schemas.alert import AlertRuleCreate, AlertCreate
        
        # Create device
        device_service = DeviceService(db_session)
        device = await device_service.create_device(
            DeviceCreate(
                name="Snooze Test Device",
                device_type="server",
                hostname="snooze-test.local"
            )
        )
        
        # Create alert rule and alert
        alert_service = AlertService(db_session)
        rule = await alert_service.create_alert_rule(
            AlertRuleCreate(
                name="Snooze Test Rule",
                device_id=device.id,
                metric_type="cpu_usage_percent",
                rule_type="threshold",
                severity="warning",
                threshold_value=80.0,
                comparison_operator="gt"
            )
        )
        
        alert = await alert_service.create_alert(
            AlertCreate(
                rule_id=rule.id,
                device_id=device.id,
                metric_type="cpu_usage_percent",
                severity="warning",
                message="Test alert message",
                trigger_value=85.0
            )
        )
        
        # Snooze alert for 30 minutes
        success = await alert_service.snooze_alert(alert.id, minutes=30)
        
        assert success is True
        
        # Verify snooze status
        alerts = await alert_service.get_alerts()
        snoozed = next((a for a in alerts if a.id == alert.id), None)
        
        assert snoozed is not None
        assert snoozed.status == "snoozed"
        assert snoozed.snoozed_until is not None


class TestE2EMetricsAggregation:
    """End-to-end tests for metrics aggregation."""
    
    @pytest.mark.e2e
    async def test_metrics_time_range_aggregation(self, client: AsyncClient, auth_headers, db_session):
        """
        Test metrics aggregation over time:
        1. Create device
        2. Ingest metrics with different timestamps
        3. Query with time range
        4. Verify aggregation
        """
        from app.services.device_service import DeviceService
        from app.services.metric_service import MetricService
        from app.schemas.device import DeviceCreate
        from app.schemas.metric import MetricCreate
        from datetime import timedelta
        
        # Create device
        device_service = DeviceService(db_session)
        device = await device_service.create_device(
            DeviceCreate(
                name="Aggregation Test Device",
                device_type="server",
                hostname="aggregation-test.local"
            )
        )
        
        # Ingest metrics over time
        metric_service = MetricService(db_session)
        base_time = datetime.utcnow() - timedelta(hours=2)
        
        metrics = []
        for i in range(12):  # 2 hours of data
            metrics.append(
                MetricCreate(
                    device_id=device.id,
                    metric_type="cpu_usage_percent",
                    value=50.0 + (i % 20),  # Varying values
                    timestamp=(base_time + timedelta(minutes=i * 10)).isoformat()
                )
            )
        
        await metric_service.ingest_metrics(metrics)
        
        # Query with different time ranges
        now = datetime.utcnow()
        
        # 1 hour range
        metrics_1h = await metric_service.get_metrics(
            device_id=device.id,
            start_time=now - timedelta(hours=1),
            end_time=now
        )
        
        # 2 hour range
        metrics_2h = await metric_service.get_metrics(
            device_id=device.id,
            start_time=now - timedelta(hours=2),
            end_time=now
        )
        
        assert len(metrics_1h) <= len(metrics_2h)
        
        # Get summary
        summary = await metric_service.get_metrics_summary(device.id, hours=24)
        
        assert len(summary) >= 1
        cpu_summary = next((s for s in summary if s.metric_type == "cpu_usage_percent"), None)
        
        assert cpu_summary is not None
        assert cpu_summary.count == 12
        assert cpu_summary.min_value >= 50.0
        assert cpu_summary.max_value <= 70.0


class TestE2ENotificationChannels:
    """End-to-end tests for notification channels."""
    
    @pytest.mark.e2e
    @pytest.mark.notification
    async def test_multi_channel_notification(self, client: AsyncClient, auth_headers, db_session):
        """
        Test multi-channel notification:
        1. Create alert rule with multiple channels
        2. Trigger alert
        3. Verify all channels would be notified
        """
        from app.services.device_service import DeviceService
        from app.services.alert_service import AlertService
        from app.services.notification_service import NotificationService
        from app.schemas.device import DeviceCreate
        from app.schemas.alert import AlertRuleCreate, AlertCreate
        from unittest.mock import AsyncMock, patch
        
        # Create device
        device_service = DeviceService(db_session)
        device = await device_service.create_device(
            DeviceCreate(
                name="Multi-Channel Device",
                device_type="server",
                hostname="multi-channel.local"
            )
        )
        
        # Create alert rule with multiple channels
        alert_service = AlertService(db_session)
        rule = await alert_service.create_alert_rule(
            AlertRuleCreate(
                name="Multi-Channel Alert",
                device_id=device.id,
                metric_type="cpu_usage_percent",
                rule_type="threshold",
                severity="warning",
                threshold_value=80.0,
                comparison_operator="gt",
                notification_channels=["email", "telegram", "discord"]
            )
        )
        
        # Create alert
        alert = await alert_service.create_alert(
            AlertCreate(
                rule_id=rule.id,
                device_id=device.id,
                metric_type="cpu_usage_percent",
                severity="warning",
                message="Multi-channel test alert",
                trigger_value=85.0
            )
        )
        
        # Test notification service
        notification_service = NotificationService()
        
        with patch.object(notification_service, '_send_email_notification', new_callable=AsyncMock) as mock_email:
            with patch.object(notification_service, '_send_telegram_notification', new_callable=AsyncMock) as mock_telegram:
                with patch.object(notification_service, '_send_discord_notification', new_callable=AsyncMock) as mock_discord:
                    mock_email.return_value = True
                    mock_telegram.return_value = True
                    mock_discord.return_value = True
                    
                    await notification_service.send_alert_notifications(alert, rule)
                    
                    mock_email.assert_called_once_with(alert, rule)
                    mock_telegram.assert_called_once_with(alert, rule)
                    mock_discord.assert_called_once_with(alert, rule)


class TestE2EDeviceLifecycle:
    """End-to-end tests for device lifecycle management."""
    
    @pytest.mark.e2e
    async def test_device_crud_lifecycle(self, client: AsyncClient, auth_headers, db_session):
        """
        Test complete device CRUD lifecycle:
        1. Create device
        2. Read device
        3. Update device
        4. Delete device
        """
        from app.services.device_service import DeviceService
        from app.schemas.device import DeviceCreate, DeviceUpdate
        
        device_service = DeviceService(db_session)
        
        # 1. Create
        device = await device_service.create_device(
            DeviceCreate(
                name="Lifecycle Test Device",
                description="Device for lifecycle testing",
                device_type="server",
                hostname="lifecycle-test.local"
            )
        )
        
        device_id = device.id
        assert device_id is not None
        
        # 2. Read
        fetched_device = await device_service.get_device(device_id)
        assert fetched_device is not None
        assert fetched_device.name == "Lifecycle Test Device"
        
        # 3. Update
        updated_device = await device_service.update_device(
            device_id,
            DeviceUpdate(
                name="Updated Lifecycle Device",
                description="Updated description"
            )
        )
        
        assert updated_device is not None
        assert updated_device.name == "Updated Lifecycle Device"
        
        # 4. Delete
        delete_result = await device_service.delete_device(device_id)
        assert delete_result is True
        
        # Verify deleted
        deleted_device = await device_service.get_device(device_id)
        assert deleted_device is None


class TestE2EAuthenticationFlow:
    """End-to-end tests for authentication flow."""
    
    @pytest.mark.e2e
    async def test_complete_auth_flow(self, client: AsyncClient):
        """
        Test complete authentication flow:
        1. Register user
        2. Login
        3. Access protected resource
        4. Logout (implicit)
        """
        import uuid
        
        unique_email = f"e2e_test_{uuid.uuid4().hex[:8]}@example.com"
        
        # 1. Register
        register_data = {
            "email": unique_email,
            "password": "e2epassword123",
            "full_name": "E2E Test User"
        }
        
        register_response = await client.post(
            "/api/v1/auth/register",
            json=register_data
        )
        
        assert register_response.status_code == 200
        user_data = register_response.json()
        assert user_data["email"] == unique_email
        
        # 2. Login
        login_data = {
            "username": unique_email,
            "password": "e2epassword123"
        }
        
        login_response = await client.post(
            "/api/v1/auth/login",
            data=login_data
        )
        
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        assert token is not None
        
        # 3. Access protected resource
        me_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["email"] == unique_email
        
        # 4. Try access without token
        unauthorized_response = await client.get("/api/v1/auth/me")
        assert unauthorized_response.status_code == 401


class TestE2EErrorHandling:
    """End-to-end tests for error handling."""
    
    @pytest.mark.e2e
    async def test_graceful_error_handling(self, client: AsyncClient):
        """
        Test graceful error handling:
        1. Invalid endpoint
        2. Invalid data
        3. Missing required fields
        """
        # 1. Invalid endpoint
        invalid_response = await client.get("/api/v1/nonexistent")
        assert invalid_response.status_code in [404, 405, 400]
        
        # 2. Invalid data
        invalid_data_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "123",  # Too short
                "full_name": "Test"
            }
        )
        assert invalid_data_response.status_code == 422
        
        # 3. Missing required fields
        missing_fields_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com"
                # Missing password
            }
        )
        assert missing_fields_response.status_code == 422
