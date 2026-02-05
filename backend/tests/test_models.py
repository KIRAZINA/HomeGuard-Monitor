import pytest
import pytest_asyncio
from datetime import datetime
from app.models.device import Device, DeviceType, DeviceStatus
from app.models.metric import Metric
from app.models.alert import AlertRule, Alert
from app.models.user import User


class TestDeviceModel:
    """Test Device model."""

    @pytest_asyncio.fixture
    async def local_device(self, db_session):
        """Create a device for testing."""
        device = Device(
            name="Test Server",
            description="Test server description",
            device_type=DeviceType.SERVER,
            hostname="test-server",
            ip_address="192.168.1.100",
            location="Test Lab",
            tags="test,server",
            status=DeviceStatus.ONLINE
        )
        db_session.add(device)
        await db_session.commit()
        await db_session.refresh(device)
        return device

    @pytest.mark.asyncio
    async def test_device_creation(self, db_session, local_device):
        """Test device model creation."""
        device = local_device
        
        assert device.id is not None
        assert device.name == "Test Server"
        assert device.device_type == DeviceType.SERVER
        assert device.status == DeviceStatus.ONLINE
        assert device.created_at is not None
        assert device.updated_at is not None

    @pytest.mark.asyncio
    async def test_device_defaults(self, db_session):
        """Test device model default values."""
        device = Device(
            name="Test Server",
            device_type=DeviceType.SERVER,
            hostname="test-server"
        )
        
        db_session.add(device)
        await db_session.commit()
        await db_session.refresh(device)
        
        assert device.status == DeviceStatus.OFFLINE  # Default status
        assert device.description is None
        assert device.ip_address is None
        assert device.location is None
        assert device.tags is None

    @pytest.mark.asyncio
    async def test_device_string_representation(self, db_session):
        """Test device string representation."""
        device = Device(
            name="Test Server",
            device_type=DeviceType.SERVER,
            hostname="test-server"
        )
        
        # Test that the device has a __repr__ method
        assert hasattr(device, '__repr__')
        repr_str = repr(device)
        assert "Test Server" in repr_str or "Device" in repr_str


class TestMetricModel:
    """Test Metric model."""

    @pytest_asyncio.fixture
    async def local_device(self, db_session):
        """Create a device for testing."""
        device = Device(
            name="Test Server",
            device_type=DeviceType.SERVER,
            hostname="test-server"
        )
        db_session.add(device)
        await db_session.commit()
        await db_session.refresh(device)
        return device

    @pytest.mark.asyncio
    async def test_metric_creation(self, db_session, local_device):
        """Test metric model creation."""
        metric = Metric(
            device_id=local_device.id,
            metric_type="cpu_usage_percent",
            value=75.5,
            unit="percent",
            tags={"core": "0"},
            timestamp=datetime.utcnow()
        )
        
        db_session.add(metric)
        await db_session.commit()
        await db_session.refresh(metric)
        
        assert metric.id is not None
        assert metric.device_id == local_device.id
        assert metric.metric_type == "cpu_usage_percent"
        assert metric.value == 75.5
        assert metric.unit == "percent"
        assert metric.tags == {"core": "0"}
        assert metric.timestamp is not None

    @pytest.mark.asyncio
    async def test_metric_defaults(self, db_session, local_device):
        """Test metric model default values."""
        metric = Metric(
            device_id=local_device.id,
            metric_type="cpu_usage_percent",
            value=75.5
        )
        
        db_session.add(metric)
        await db_session.commit()
        await db_session.refresh(metric)
        
        assert metric.unit is None
        assert metric.tags is None
        assert metric.timestamp is not None  # Should have default timestamp

    @pytest.mark.asyncio
    async def test_metric_device_relationship(self, db_session, local_device):
        """Test metric-device relationship."""
        metric = Metric(
            device_id=local_device.id,
            metric_type="cpu_usage_percent",
            value=75.5
        )
        
        db_session.add(metric)
        await db_session.commit()
        await db_session.refresh(metric)
        
        assert metric.device.name == local_device.name
        assert metric.device.hostname == local_device.hostname


class TestAlertRuleModel:
    """Test AlertRule model."""

    @pytest_asyncio.fixture
    async def local_device(self, db_session):
        """Create a device for testing."""
        device = Device(
            name="Test Server",
            device_type=DeviceType.SERVER,
            hostname="test-server"
        )
        db_session.add(device)
        await db_session.commit()
        await db_session.refresh(device)
        return device

    @pytest.mark.asyncio
    async def test_alert_rule_creation(self, db_session, local_device):
        """Test alert rule model creation."""
        rule = AlertRule(
            name="High CPU Alert",
            description="Alert when CPU is high",
            device_id=local_device.id,
            metric_type="cpu_usage_percent",
            rule_type="threshold",
            severity="warning",
            threshold_value=80.0,
            comparison_operator="gt",
            evaluation_window_minutes=5,
            notification_channels=["email", "telegram"],
            enabled=True
        )
        
        db_session.add(rule)
        await db_session.commit()
        await db_session.refresh(rule)
        
        assert rule.id is not None
        assert rule.name == "High CPU Alert"
        assert rule.device_id == local_device.id
        assert rule.threshold_value == 80.0
        assert rule.enabled is True
        assert rule.created_at is not None

    @pytest.mark.asyncio
    async def test_alert_rule_defaults(self, db_session, local_device):
        """Test alert rule model default values."""
        rule = AlertRule(
            name="Test Alert",
            device_id=local_device.id,
            metric_type="cpu_usage_percent",
            rule_type="threshold",
            severity="warning"
        )
        
        db_session.add(rule)
        await db_session.commit()
        await db_session.refresh(rule)
        
        assert rule.evaluation_window_minutes == 5  # Default value
        assert rule.enabled is True  # Default value
        assert rule.notification_channels == []  # Default empty list

    @pytest.mark.asyncio
    async def test_alert_rule_device_relationship(self, db_session, local_device):
        """Test alert rule-device relationship."""
        rule = AlertRule(
            name="Test Alert",
            device_id=local_device.id,
            metric_type="cpu_usage_percent",
            rule_type="threshold",
            severity="warning"
        )
        
        db_session.add(rule)
        await db_session.commit()
        await db_session.refresh(rule)
        
        assert rule.device.name == local_device.name


class TestAlertModel:
    """Test Alert model."""

    @pytest_asyncio.fixture
    async def local_device_and_rule(self, db_session):
        """Create a device and rule for testing."""
        device = Device(
            name="Test Server",
            device_type=DeviceType.SERVER,
            hostname="test-server"
        )
        db_session.add(device)
        await db_session.commit()
        await db_session.refresh(device)
        
        rule = AlertRule(
            name="Test Rule",
            device_id=device.id,
            metric_type="cpu_usage_percent",
            rule_type="threshold",
            severity="warning"
        )
        db_session.add(rule)
        await db_session.commit()
        await db_session.refresh(rule)
        
        return device, rule

    @pytest.mark.asyncio
    async def test_alert_creation(self, db_session, local_device_and_rule):
        """Test alert model creation."""
        device, rule = local_device_and_rule
        
        alert = Alert(
            rule_id=rule.id,
            device_id=device.id,
            metric_type="cpu_usage_percent",
            severity="warning",
            status="active",
            message="CPU usage is high",
            trigger_value=85.0,
            triggered_at=datetime.utcnow()
        )
        
        db_session.add(alert)
        await db_session.commit()
        await db_session.refresh(alert)
        
        assert alert.id is not None
        assert alert.rule_id == rule.id
        assert alert.device_id == device.id
        assert alert.status == "active"
        assert alert.trigger_value == 85.0
        assert alert.triggered_at is not None

    @pytest.mark.asyncio
    async def test_alert_defaults(self, db_session, local_device_and_rule):
        """Test alert model default values."""
        device, rule = local_device_and_rule
        
        alert = Alert(
            rule_id=rule.id,
            device_id=device.id,
            metric_type="cpu_usage_percent",
            severity="warning",
            message="Test alert",
            trigger_value=80.0
        )
        
        db_session.add(alert)
        await db_session.commit()
        await db_session.refresh(alert)
        
        assert alert.status == "active"  # Default status
        assert alert.acknowledged_at is None
        assert alert.acknowledged_by is None
        assert alert.resolved_at is None
        assert alert.snoozed_until is None
        assert alert.triggered_at is not None  # Should have default timestamp

    @pytest.mark.asyncio
    async def test_alert_relationships(self, db_session, local_device_and_rule):
        """Test alert relationships."""
        device, rule = local_device_and_rule
        
        alert = Alert(
            rule_id=rule.id,
            device_id=device.id,
            metric_type="cpu_usage_percent",
            severity="warning",
            message="Test alert",
            trigger_value=80.0
        )
        
        db_session.add(alert)
        await db_session.commit()
        await db_session.refresh(alert)
        
        assert alert.rule.name == rule.name
        assert alert.device.name == device.name


class TestUserModel:
    """Test User model."""

    @pytest.mark.asyncio
    async def test_user_creation(self, db_session):
        """Test user model creation."""
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password="hashed_password_here",
            is_active=True
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.hashed_password == "hashed_password_here"
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None

    @pytest.mark.asyncio
    async def test_user_defaults(self, db_session):
        """Test user model default values."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password_here"
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.full_name is None
        assert user.is_active is True  # Default value

    @pytest.mark.asyncio
    async def test_user_email_unique(self, db_session):
        """Test user email uniqueness constraint."""
        user1 = User(
            email="duplicate@example.com",
            hashed_password="password1"
        )
        
        user2 = User(
            email="duplicate@example.com",
            hashed_password="password2"
        )
        
        db_session.add(user1)
        await db_session.commit()
        
        db_session.add(user2)
        
        # This should raise an integrity error due to unique constraint
        with pytest.raises(Exception):  # Could be different exception types
            await db_session.commit()
