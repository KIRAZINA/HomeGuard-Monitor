import pytest
from datetime import datetime, timedelta
from app.services.device_service import DeviceService
from app.services.metric_service import MetricService
from app.services.alert_service import AlertService
from app.services.auth_service import AuthService
from app.schemas.device import DeviceCreate, DeviceUpdate
from app.schemas.metric import MetricCreate, MetricQuery
from app.schemas.alert import AlertRuleCreate, AlertCreate
from app.schemas.user import UserCreate
from app.models.device import DeviceType, DeviceStatus


class TestDeviceService:
    """Test device service layer."""

    @pytest.mark.asyncio
    async def test_create_device(self, db_session):
        """Test device creation in service layer."""
        device_service = DeviceService(db_session)
        device_data = DeviceCreate(
            name="Test Server",
            description="Test server",
            device_type=DeviceType.SERVER,
            hostname="test-server",
            ip_address="192.168.1.100"
        )
        
        device = await device_service.create_device(device_data)
        
        assert device.name == device_data.name
        assert device.device_type == device_data.device_type
        assert device.hostname == device_data.hostname
        assert device.status == DeviceStatus.OFFLINE  # Default status
        assert device.id is not None

    @pytest.mark.asyncio
    async def test_get_device(self, db_session, test_device):
        """Test getting device by ID."""
        device_service = DeviceService(db_session)
        
        device = await device_service.get_device(test_device.id)
        
        assert device is not None
        assert device.id == test_device.id
        assert device.name == test_device.name

    async def test_get_device_not_found(self, db_session):
        """Test getting non-existent device."""
        device_service = DeviceService(db_session)
        
        device = await device_service.get_device(99999)
        
        assert device is None

    async def test_get_devices(self, db_session, test_device):
        """Test getting list of devices."""
        device_service = DeviceService(db_session)
        
        devices = await device_service.get_devices()
        
        assert len(devices) >= 1
        device_ids = [device.id for device in devices]
        assert test_device.id in device_ids

    @pytest.mark.asyncio
    async def test_update_device(self, db_session, test_device):
        """Test device update."""
        device_service = DeviceService(db_session)
        update_data = DeviceUpdate(
            name="Updated Name",
            description="Updated description"
        )
        
        device = await device_service.update_device(test_device.id, update_data)
        
        assert device is not None
        assert device.name == update_data.name
        assert device.description == update_data.description
        assert device.hostname == test_device.hostname  # Unchanged

    @pytest.mark.asyncio
    async def test_delete_device(self, db_session, test_device):
        """Test device deletion."""
        device_service = DeviceService(db_session)
        
        success = await device_service.delete_device(test_device.id)
        
        assert success is True
        
        # Verify device is deleted
        device = await device_service.get_device(test_device.id)
        assert device is None

    @pytest.mark.asyncio
    async def test_update_device_status(self, db_session, test_device):
        """Test device status update."""
        device_service = DeviceService(db_session)
        
        success = await device_service.update_device_status(
            test_device.id, 
            DeviceStatus.ONLINE
        )
        
        assert success is True
        
        device = await device_service.get_device(test_device.id)
        assert device.status == DeviceStatus.ONLINE


class TestMetricService:
    """Test metric service layer."""

    @pytest.mark.asyncio
    async def test_ingest_metrics(self, db_session, test_device):
        """Test metrics ingestion."""
        metric_service = MetricService(db_session)
        
        metrics_data = [
            MetricCreate(
                device_id=test_device.id,
                metric_type="cpu_usage_percent",
                value=75.5,
                unit="percent"
            ),
            MetricCreate(
                device_id=test_device.id,
                metric_type="memory_usage_percent",
                value=60.2,
                unit="percent"
            )
        ]
        
        await metric_service.ingest_metrics(metrics_data)
        
        # Verify metrics were stored
        query = MetricQuery(
            device_id=test_device.id,
            start_time=datetime.utcnow() - timedelta(minutes=5),
            end_time=datetime.utcnow()
        )
        
        stored_metrics = await metric_service.get_metrics(query)
        assert len(stored_metrics) >= 2

    @pytest.mark.asyncio
    async def test_get_metrics_with_filters(self, db_session, test_metrics):
        """Test getting metrics with filters."""
        metric_service = MetricService(db_session)
        device_id = test_metrics[0].device_id
        
        query = MetricQuery(
            device_id=device_id,
            metric_type="cpu_usage_percent",
            start_time=datetime.utcnow() - timedelta(hours=2),
            end_time=datetime.utcnow(),
            limit=5
        )
        
        metrics = await metric_service.get_metrics(query)
        
        assert len(metrics) <= 5
        assert all(m.device_id == device_id for m in metrics)
        assert all(m.metric_type == "cpu_usage_percent" for m in metrics)

    @pytest.mark.asyncio
    async def test_get_latest_metrics(self, db_session, test_device):
        """Test getting latest metrics."""
        metric_service = MetricService(db_session)
        
        # Create some test metrics
        metrics_data = [
            MetricCreate(
                device_id=test_device.id,
                metric_type="cpu_usage_percent",
                value=50.0
            ),
            MetricCreate(
                device_id=test_device.id,
                metric_type="memory_usage_percent",
                value=60.0
            )
        ]
        
        await metric_service.ingest_metrics(metrics_data)
        
        latest_metrics = await metric_service.get_latest_metrics(test_device.id)
        
        assert len(latest_metrics) >= 2
        metric_types = [m.metric_type for m in latest_metrics]
        assert "cpu_usage_percent" in metric_types
        assert "memory_usage_percent" in metric_types

    @pytest.mark.asyncio
    async def test_get_metrics_summary(self, db_session, test_device):
        """Test metrics summary calculation."""
        metric_service = MetricService(db_session)
        
        # Create test metrics with different values
        metrics_data = []
        for i in range(10):
            metrics_data.append(
                MetricCreate(
                    device_id=test_device.id,
                    metric_type="cpu_usage_percent",
                    value=50.0 + i * 2
                )
            )
        
        await metric_service.ingest_metrics(metrics_data)
        
        summary = await metric_service.get_metrics_summary(test_device.id, 24)
        
        assert len(summary) >= 1
        cpu_summary = next(s for s in summary if s.metric_type == "cpu_usage_percent")
        
        assert cpu_summary.count == 10
        assert cpu_summary.min_value == 50.0
        assert cpu_summary.max_value == 68.0
        assert cpu_summary.avg_value == 59.0


class TestAlertService:
    """Test alert service layer."""

    @pytest.mark.asyncio
    async def test_create_alert_rule(self, db_session, test_device):
        """Test alert rule creation."""
        alert_service = AlertService(db_session)
        
        rule_data = AlertRuleCreate(
            name="High CPU",
            device_id=test_device.id,
            metric_type="cpu_usage_percent",
            rule_type="threshold",
            severity="warning",
            threshold_value=80.0,
            comparison_operator="gt"
        )
        
        rule = await alert_service.create_alert_rule(rule_data)
        
        assert rule.name == rule_data.name
        assert rule.metric_type == rule_data.metric_type
        assert rule.threshold_value == rule_data.threshold_value
        assert rule.id is not None

    @pytest.mark.asyncio
    async def test_get_alert_rules(self, db_session, test_device):
        """Test getting alert rules."""
        alert_service = AlertService(db_session)
        
        # Create a test rule
        rule_data = AlertRuleCreate(
            name="Test Rule",
            device_id=test_device.id,
            metric_type="cpu_usage_percent",
            rule_type="threshold",
            severity="warning",
            threshold_value=80.0,
            comparison_operator="gt"
        )
        
        await alert_service.create_alert_rule(rule_data)
        
        rules = await alert_service.get_alert_rules()
        
        assert len(rules) >= 1
        assert any(rule.name == "Test Rule" for rule in rules)

    @pytest.mark.asyncio
    async def test_create_alert(self, db_session, test_device):
        """Test alert creation."""
        alert_service = AlertService(db_session)
        
        # First create a rule
        rule_data = AlertRuleCreate(
            name="Test Rule",
            device_id=test_device.id,
            metric_type="cpu_usage_percent",
            rule_type="threshold",
            severity="warning",
            threshold_value=80.0,
            comparison_operator="gt"
        )
        
        rule = await alert_service.create_alert_rule(rule_data)
        
        # Now create an alert
        alert_data = AlertCreate(
            rule_id=rule.id,
            device_id=test_device.id,
            metric_type="cpu_usage_percent",
            severity="warning",
            message="CPU usage is high",
            trigger_value=85.0
        )
        
        alert = await alert_service.create_alert(alert_data)
        
        assert alert.rule_id == rule.id
        assert alert.device_id == test_device.id
        assert alert.message == alert_data.message
        assert alert.trigger_value == alert_data.trigger_value
        assert alert.status == "active"

    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, db_session, test_device):
        """Test alert acknowledgment."""
        alert_service = AlertService(db_session)
        
        # Create rule and alert
        rule_data = AlertRuleCreate(
            name="Test Rule",
            device_id=test_device.id,
            metric_type="cpu_usage_percent",
            rule_type="threshold",
            severity="warning",
            threshold_value=80.0,
            comparison_operator="gt"
        )
        
        rule = await alert_service.create_alert_rule(rule_data)
        
        alert_data = AlertCreate(
            rule_id=rule.id,
            device_id=test_device.id,
            metric_type="cpu_usage_percent",
            severity="warning",
            message="CPU usage is high",
            trigger_value=85.0
        )
        
        alert = await alert_service.create_alert(alert_data)
        
        # Acknowledge the alert
        success = await alert_service.acknowledge_alert(alert.id, "test_user")
        
        assert success is True
        
        # Verify alert is acknowledged
        alerts = await alert_service.get_alerts()
        acknowledged_alert = next(a for a in alerts if a.id == alert.id)
        assert acknowledged_alert.status == "acknowledged"
        assert acknowledged_alert.acknowledged_by == "test_user"

    @pytest.mark.asyncio
    async def test_snooze_alert(self, db_session, test_device):
        """Test alert snoozing."""
        alert_service = AlertService(db_session)
        
        # Create rule and alert
        rule_data = AlertRuleCreate(
            name="Test Rule",
            device_id=test_device.id,
            metric_type="cpu_usage_percent",
            rule_type="threshold",
            severity="warning",
            threshold_value=80.0,
            comparison_operator="gt"
        )
        
        rule = await alert_service.create_alert_rule(rule_data)
        
        alert_data = AlertCreate(
            rule_id=rule.id,
            device_id=test_device.id,
            metric_type="cpu_usage_percent",
            severity="warning",
            message="CPU usage is high",
            trigger_value=85.0
        )
        
        alert = await alert_service.create_alert(alert_data)
        
        # Snooze the alert
        success = await alert_service.snooze_alert(alert.id, 30)
        
        assert success is True
        
        # Verify alert is snoozed
        alerts = await alert_service.get_alerts()
        snoozed_alert = next(a for a in alerts if a.id == alert.id)
        assert snoozed_alert.status == "snoozed"
        assert snoozed_alert.snoozed_until is not None


class TestAuthService:
    """Test authentication service layer."""

    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        """Test user creation."""
        auth_service = AuthService(db_session)
        
        user_data = UserCreate(
            email="test@example.com",
            password="testpassword123",
            full_name="Test User"
        )
        
        user = await auth_service.create_user(user_data)
        
        assert user.email == user_data.email
        assert user.full_name == user_data.full_name
        assert user.is_active is True
        assert user.hashed_password != user_data.password  # Should be hashed
        assert user.id is not None

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, db_session):
        """Test successful user authentication."""
        auth_service = AuthService(db_session)
        
        # Create user first
        user_data = UserCreate(
            email="auth@example.com",
            password="authpassword123",
            full_name="Auth User"
        )
        
        await auth_service.create_user(user_data)
        
        # Now authenticate
        user = await auth_service.authenticate_user("auth@example.com", "authpassword123")
        
        assert user is not None
        assert user.email == user_data.email

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(self, db_session):
        """Test authentication with invalid password."""
        auth_service = AuthService(db_session)
        
        # Create user first
        user_data = UserCreate(
            email="auth2@example.com",
            password="authpassword123",
            full_name="Auth User 2"
        )
        
        await auth_service.create_user(user_data)
        
        # Try authenticate with wrong password
        user = await auth_service.authenticate_user("auth2@example.com", "wrongpassword")
        
        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_nonexistent(self, db_session):
        """Test authentication with non-existent user."""
        auth_service = AuthService(db_session)
        
        user = await auth_service.authenticate_user("nonexistent@example.com", "password")
        
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, db_session):
        """Test getting user by email."""
        auth_service = AuthService(db_session)
        
        # Create user first
        user_data = UserCreate(
            email="get@example.com",
            password="password123",
            full_name="Get User"
        )
        
        created_user = await auth_service.create_user(user_data)
        
        # Get user by email
        user = await auth_service.get_user_by_email("get@example.com")
        
        assert user is not None
        assert user.id == created_user.id
        assert user.email == user_data.email

    @pytest.mark.asyncio
    async def test_create_access_token(self, db_session):
        """Test JWT token creation."""
        auth_service = AuthService(db_session)
        
        token = auth_service.create_access_token(
            data={"sub": "test@example.com"}
        )
        
        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.asyncio
    async def test_verify_password(self, db_session):
        """Test password verification."""
        auth_service = AuthService(db_session)
        
        password = "testpassword123"
        hashed = auth_service.get_password_hash(password)
        
        assert auth_service.verify_password(password, hashed) is True
        assert auth_service.verify_password("wrongpassword", hashed) is False
