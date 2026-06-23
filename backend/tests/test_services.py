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
    async def test_create_device(self, db_session, test_user):
        """Test device creation in service layer."""
        device_service = DeviceService(db_session)
        device_data = DeviceCreate(
            name="Test Server",
            description="Test server",
            device_type=DeviceType.SERVER,
            hostname="test-server",
            ip_address="192.168.1.100",
        )

        device = await device_service.create_device(device_data, user_id=test_user.id)

        assert device.name == device_data.name
        assert device.device_type == device_data.device_type
        assert device.hostname == device_data.hostname
        assert device.status == DeviceStatus.OFFLINE
        assert device.id is not None

    @pytest.mark.asyncio
    async def test_get_device(self, db_session, test_device, test_user):
        """Test getting device by ID."""
        device_service = DeviceService(db_session)

        device = await device_service.get_device(test_device.id, user_id=test_user.id)

        assert device is not None
        assert device.id == test_device.id
        assert device.name == test_device.name

    @pytest.mark.asyncio
    async def test_get_device_not_found(self, db_session, test_user):
        """Test getting non-existent device."""
        device_service = DeviceService(db_session)

        device = await device_service.get_device(99999, user_id=test_user.id)

        assert device is None

    @pytest.mark.asyncio
    async def test_get_devices(self, db_session, test_device, test_user):
        """Test getting list of devices."""
        device_service = DeviceService(db_session)

        devices = await device_service.get_devices(user_id=test_user.id)

        assert len(devices) >= 1
        device_ids = [d.id for d in devices]
        assert test_device.id in device_ids

    @pytest.mark.asyncio
    async def test_update_device(self, db_session, test_device, test_user):
        """Test device update."""
        device_service = DeviceService(db_session)
        update_data = DeviceUpdate(name="Updated Name", description="Updated description")

        device = await device_service.update_device(
            test_device.id, update_data, user_id=test_user.id
        )

        assert device is not None
        assert device.name == update_data.name
        assert device.description == update_data.description
        assert device.hostname == test_device.hostname

    @pytest.mark.asyncio
    async def test_delete_device(self, db_session, test_device, test_user):
        """Test device deletion."""
        device_service = DeviceService(db_session)

        success = await device_service.delete_device(test_device.id, user_id=test_user.id)

        assert success is True

        device = await device_service.get_device(test_device.id, user_id=test_user.id)
        assert device is None

    @pytest.mark.asyncio
    async def test_update_device_status(self, db_session, test_device, test_user):
        """Test device status update."""
        device_service = DeviceService(db_session)

        success = await device_service.update_device_status(test_device.id, DeviceStatus.ONLINE)

        assert success is True

        device = await device_service.get_device(test_device.id, user_id=test_user.id)
        assert device.status == DeviceStatus.ONLINE


class TestMetricService:
    """Test metric service layer."""

    @pytest.mark.asyncio
    async def test_ingest_metrics(self, db_session, test_device):
        """Test metric ingestion."""
        metric_service = MetricService(db_session)
        metrics_data = [
            MetricCreate(
                device_id=test_device.id,
                metric_type="cpu_usage_percent",
                value=75.5,
                unit="percent",
            )
        ]

        result = await metric_service.ingest_metrics(metrics_data)

        assert result is not None
        assert result["ingested"] == 1

    @pytest.mark.asyncio
    async def test_get_metrics(self, db_session, test_device):
        """Test metrics retrieval."""
        metric_service = MetricService(db_session)
        metrics_data = [
            MetricCreate(
                device_id=test_device.id, metric_type="cpu_usage_percent", value=50.0 + i * 10
            )
            for i in range(5)
        ]
        await metric_service.ingest_metrics(metrics_data)

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        metrics = await metric_service.get_metrics(
            MetricQuery(device_id=test_device.id, start_time=start_time, end_time=end_time)
        )

        assert len(metrics) == 5
        assert all(m.device_id == test_device.id for m in metrics)

    @pytest.mark.asyncio
    async def test_get_latest_metrics(self, db_session, test_device):
        """Test latest metrics retrieval."""
        metric_service = MetricService(db_session)
        metrics_data = [
            MetricCreate(
                device_id=test_device.id,
                metric_type="cpu_usage_percent",
                value=50.0 + i * 10,
                timestamp=datetime.utcnow(),
            )
            for i in range(3)
        ]
        await metric_service.ingest_metrics(metrics_data)

        latest = await metric_service.get_latest_metrics(test_device.id)

        assert len(latest) >= 1
        assert all(m.device_id == test_device.id for m in latest)

    @pytest.mark.asyncio
    async def test_get_metrics_summary(self, db_session, test_device):
        """Test metrics summary."""
        metric_service = MetricService(db_session)
        metrics_data = [
            MetricCreate(device_id=test_device.id, metric_type="cpu_usage_percent", value=float(v))
            for v in [50, 60, 70, 80, 90]
        ]
        await metric_service.ingest_metrics(metrics_data)

        summary = await metric_service.get_metrics_summary(test_device.id)

        assert len(summary) >= 1
        s = next(s for s in summary if s.metric_type == "cpu_usage_percent")
        assert s.min_value == 50.0
        assert s.max_value == 90.0
        assert s.count >= 5


class TestAlertService:
    """Test alert service layer."""

    @pytest.mark.asyncio
    async def test_create_alert_rule(self, db_session, test_device):
        """Test alert rule creation."""
        alert_service = AlertService(db_session)
        rule_data = AlertRuleCreate(
            name="High CPU Alert",
            device_id=test_device.id,
            metric_type="cpu_usage_percent",
            rule_type="threshold",
            severity="warning",
            threshold_value=80.0,
            comparison_operator="gt",
            notification_channels=["email"],
        )

        rule = await alert_service.create_alert_rule(rule_data)

        assert rule.name == rule_data.name
        assert rule.device_id == test_device.id
        assert rule.id is not None

    @pytest.mark.asyncio
    async def test_create_alert(self, db_session, test_device):
        """Test alert creation."""
        alert_service = AlertService(db_session)
        rule_data = AlertRuleCreate(
            name="Test Rule",
            device_id=test_device.id,
            metric_type="cpu_usage_percent",
            rule_type="threshold",
            severity="warning",
            threshold_value=80.0,
            comparison_operator="gt",
            notification_channels=["email"],
        )
        rule = await alert_service.create_alert_rule(rule_data)

        alert_data = AlertCreate(
            rule_id=rule.id,
            device_id=test_device.id,
            metric_type="cpu_usage_percent",
            severity="warning",
            message="High CPU usage detected",
            trigger_value=85.0,
        )
        alert = await alert_service.create_alert(alert_data)

        assert alert.rule_id == rule.id
        assert alert.device_id == test_device.id
        assert alert.status == "active"

    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, db_session, test_device):
        """Test alert acknowledgment."""
        alert_service = AlertService(db_session)
        rule_data = AlertRuleCreate(
            name="Test Rule",
            device_id=test_device.id,
            metric_type="cpu_usage_percent",
            rule_type="threshold",
            severity="warning",
            threshold_value=80.0,
            comparison_operator="gt",
            notification_channels=["email"],
        )
        rule = await alert_service.create_alert_rule(rule_data)

        alert = await alert_service.create_alert(
            AlertCreate(
                rule_id=rule.id,
                device_id=test_device.id,
                metric_type="cpu_usage_percent",
                severity="warning",
                message="Test alert",
                trigger_value=85.0,
            )
        )

        success = await alert_service.acknowledge_alert(alert.id)

        assert success is True

    @pytest.mark.asyncio
    async def test_resolve_alert(self, db_session, test_device):
        """Test alert resolution."""
        alert_service = AlertService(db_session)
        rule_data = AlertRuleCreate(
            name="Test Rule",
            device_id=test_device.id,
            metric_type="cpu_usage_percent",
            rule_type="threshold",
            severity="warning",
            threshold_value=80.0,
            comparison_operator="gt",
            notification_channels=["email"],
        )
        rule = await alert_service.create_alert_rule(rule_data)

        alert = await alert_service.create_alert(
            AlertCreate(
                rule_id=rule.id,
                device_id=test_device.id,
                metric_type="cpu_usage_percent",
                severity="warning",
                message="Test alert",
                trigger_value=85.0,
            )
        )

        success = await alert_service.resolve_alert(alert.id)

        assert success is True
