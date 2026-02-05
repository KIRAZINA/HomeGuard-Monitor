import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from app.schemas.device import DeviceCreate
from app.schemas.metric import MetricCreate
from app.schemas.alert import AlertRuleCreate


class TestIntegration:
    """Integration tests for the complete workflow."""

    async def test_complete_monitoring_workflow(self, client: AsyncClient, auth_headers):
        """Test complete monitoring workflow: device -> metrics -> alerts."""
        
        # 1. Register a device
        device_data = {
            "name": "Integration Test Server",
            "description": "Server for integration testing",
            "device_type": "server",
            "hostname": "integration-test.local",
            "ip_address": "192.168.1.200"
        }
        
        device_response = await client.post(
            "/api/v1/devices/", 
            json=device_data, 
            headers=auth_headers
        )
        
        assert device_response.status_code == 200
        device = device_response.json()
        device_id = device["id"]
        
        # 2. Create an alert rule
        rule_data = {
            "name": "Integration Test Alert",
            "device_id": device_id,
            "metric_type": "cpu_usage_percent",
            "rule_type": "threshold",
            "severity": "warning",
            "threshold_value": 75.0,
            "comparison_operator": "gt",
            "notification_channels": ["email"]
        }
        
        rule_response = await client.post(
            "/api/v1/alerts/rules", 
            json=rule_data, 
            headers=auth_headers
        )
        
        assert rule_response.status_code == 200
        rule = rule_response.json()
        rule_id = rule["id"]
        
        # 3. Ingest metrics that should trigger the alert
        metrics_data = [
            {
                "device_id": device_id,
                "metric_type": "cpu_usage_percent",
                "value": 80.0,  # Above threshold
                "unit": "percent",
                "timestamp": (datetime.utcnow() - timedelta(minutes=2)).isoformat()
            },
            {
                "device_id": device_id,
                "metric_type": "memory_usage_percent",
                "value": 60.0,
                "unit": "percent",
                "timestamp": (datetime.utcnow() - timedelta(minutes=1)).isoformat()
            }
        ]
        
        metrics_response = await client.post(
            "/api/v1/metrics/ingest", 
            json=metrics_data, 
            headers=auth_headers
        )
        
        assert metrics_response.status_code == 200
        
        # 4. Verify metrics were stored
        stored_metrics_response = await client.get(
            f"/api/v1/metrics/?device_id={device_id}", 
            headers=auth_headers
        )
        
        assert stored_metrics_response.status_code == 200
        stored_metrics = stored_metrics_response.json()
        assert len(stored_metrics) >= 2
        
        # 5. Get latest metrics
        latest_response = await client.get(
            f"/api/v1/metrics/device/{device_id}/latest", 
            headers=auth_headers
        )
        
        assert latest_response.status_code == 200
        latest_metrics = latest_response.json()
        assert len(latest_metrics) >= 2
        
        # 6. Get metrics summary
        summary_response = await client.get(
            f"/api/v1/metrics/device/{device_id}/summary", 
            headers=auth_headers
        )
        
        assert summary_response.status_code == 200
        summary = summary_response.json()
        assert isinstance(summary, list)
        
        # 7. Verify alert rule exists
        rules_response = await client.get("/api/v1/alerts/rules", headers=auth_headers)
        assert rules_response.status_code == 200
        rules = rules_response.json()
        assert any(rule["id"] == rule_id for rule in rules)
        
        # 8. Update device status
        update_response = await client.put(
            f"/api/v1/devices/{device_id}", 
            json={"status": "online"}, 
            headers=auth_headers
        )
        
        assert update_response.status_code == 200
        updated_device = update_response.json()
        assert updated_device["status"] == "online"

    async def test_multi_device_monitoring(self, client: AsyncClient, auth_headers):
        """Test monitoring multiple devices."""
        devices = []
        
        # Create multiple devices
        for i in range(3):
            device_data = {
                "name": f"Test Device {i+1}",
                "description": f"Test device number {i+1}",
                "device_type": "server",
                "hostname": f"test-device-{i+1}.local",
                "ip_address": f"192.168.1.{201+i}"
            }
            
            response = await client.post(
                "/api/v1/devices/", 
                json=device_data, 
                headers=auth_headers
            )
            
            assert response.status_code == 200
            devices.append(response.json())
        
        # Ingest metrics for all devices
        for device in devices:
            metrics_data = [
                {
                    "device_id": device["id"],
                    "metric_type": "cpu_usage_percent",
                    "value": 50.0 + (device["id"] * 5),
                    "unit": "percent"
                }
            ]
            
            response = await client.post(
                "/api/v1/metrics/ingest", 
                json=metrics_data, 
                headers=auth_headers
            )
            
            assert response.status_code == 200
        
        # Verify all devices have metrics
        all_devices_response = await client.get("/api/v1/devices/", headers=auth_headers)
        assert all_devices_response.status_code == 200
        all_devices = all_devices_response.json()
        assert len(all_devices) >= 3
        
        # Get metrics for each device
        for device in devices:
            metrics_response = await client.get(
                f"/api/v1/metrics/?device_id={device['id']}", 
                headers=auth_headers
            )
            
            assert metrics_response.status_code == 200
            metrics = metrics_response.json()
            assert len(metrics) >= 1
            assert metrics[0]["device_id"] == device["id"]

    async def test_alert_rule_scenarios(self, client: AsyncClient, auth_headers):
        """Test different alert rule scenarios."""
        
        # Create a device for testing
        device_data = {
            "name": "Alert Test Device",
            "device_type": "server",
            "hostname": "alert-test.local"
        }
        
        device_response = await client.post(
            "/api/v1/devices/", 
            json=device_data, 
            headers=auth_headers
        )
        
        device = device_response.json()
        device_id = device["id"]
        
        # Test different alert rule configurations
        alert_rules = [
            {
                "name": "Greater Than Alert",
                "device_id": device_id,
                "metric_type": "cpu_usage_percent",
                "rule_type": "threshold",
                "severity": "warning",
                "threshold_value": 80.0,
                "comparison_operator": "gt"
            },
            {
                "name": "Less Than Alert",
                "device_id": device_id,
                "metric_type": "memory_usage_percent",
                "rule_type": "threshold",
                "severity": "info",
                "threshold_value": 20.0,
                "comparison_operator": "lt"
            },
            {
                "name": "Anomaly Detection Alert",
                "device_id": device_id,
                "metric_type": "disk_usage_percent",
                "rule_type": "anomaly",
                "severity": "critical"
            }
        ]
        
        created_rules = []
        
        for rule_data in alert_rules:
            response = await client.post(
                "/api/v1/alerts/rules", 
                json=rule_data, 
                headers=auth_headers
            )
            
            assert response.status_code == 200
            created_rules.append(response.json())
        
        # Verify all rules were created
        rules_response = await client.get("/api/v1/alerts/rules", headers=auth_headers)
        assert rules_response.status_code == 200
        all_rules = rules_response.json()
        
        for created_rule in created_rules:
            assert any(rule["id"] == created_rule["id"] for rule in all_rules)

    async def test_metrics_time_range_queries(self, client: AsyncClient, auth_headers):
        """Test querying metrics with different time ranges."""
        
        # Create a device
        device_data = {
            "name": "Time Range Test Device",
            "device_type": "server",
            "hostname": "time-range-test.local"
        }
        
        device_response = await client.post(
            "/api/v1/devices/", 
            json=device_data, 
            headers=auth_headers
        )
        
        device = device_response.json()
        device_id = device["id"]
        
        # Create metrics with different timestamps
        base_time = datetime.utcnow() - timedelta(hours=2)
        metrics_data = []
        
        for i in range(12):  # 2 hours of data, every 10 minutes
            metrics_data.append({
                "device_id": device_id,
                "metric_type": "cpu_usage_percent",
                "value": 50.0 + (i % 20),
                "timestamp": (base_time + timedelta(minutes=i*10)).isoformat()
            })
        
        # Ingest metrics
        response = await client.post(
            "/api/v1/metrics/ingest", 
            json=metrics_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Query with different time ranges
        time_ranges = [
            ("1 hour", 1),
            ("2 hours", 2),
            ("6 hours", 6)
        ]
        
        for range_name, hours in time_ranges:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            response = await client.get(
                f"/api/v1/metrics/?device_id={device_id}&"
                f"start_time={start_time.isoformat()}&"
                f"end_time={end_time.isoformat()}", 
                headers=auth_headers
            )
            
            assert response.status_code == 200
            metrics = response.json()
            assert isinstance(metrics, list)
            # Should have metrics within the time range

    async def test_error_handling_workflow(self, client: AsyncClient):
        """Test error handling in various scenarios."""
        
        # Test unauthorized access
        response = await client.get("/api/v1/devices/")
        assert response.status_code == 401
        
        response = await client.post("/api/v1/devices/", json={"name": "Test"})
        assert response.status_code == 401
        
        # Test invalid data
        auth_response = await client.post("/api/v1/auth/register", json={
            "email": "invalid-email",
            "password": "123"  # Too short
        })
        assert auth_response.status_code == 422
        
        # Test non-existent resources
        # First create a user to get auth headers
        await client.post("/api/v1/auth/register", json={
            "email": "error-test@example.com",
            "password": "testpassword123",
            "full_name": "Error Test User"
        })
        
        login_response = await client.post("/api/v1/auth/login", data={
            "username": "error-test@example.com",
            "password": "testpassword123"
        })
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test non-existent device
        response = await client.get("/api/v1/devices/99999", headers=headers)
        assert response.status_code == 404
        
        # Test non-existent alert
        response = await client.get("/api/v1/alerts/rules/99999", headers=headers)
        assert response.status_code == 404

    async def test_performance_with_large_dataset(self, client: AsyncClient, auth_headers):
        """Test performance with larger datasets."""
        
        # Create a device
        device_data = {
            "name": "Performance Test Device",
            "device_type": "server",
            "hostname": "perf-test.local"
        }
        
        device_response = await client.post(
            "/api/v1/devices/", 
            json=device_data, 
            headers=auth_headers
        )
        
        device = device_response.json()
        device_id = device["id"]
        
        # Ingest a large batch of metrics
        large_metrics_batch = []
        for i in range(500):  # 500 metrics
            large_metrics_batch.append({
                "device_id": device_id,
                "metric_type": "cpu_usage_percent",
                "value": 50.0 + (i % 50)
            })
        
        response = await client.post(
            "/api/v1/metrics/ingest", 
            json=large_metrics_batch, 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Query metrics with limit
        response = await client.get(
            f"/api/v1/metrics/?device_id={device_id}&limit=100", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        metrics = response.json()
        assert len(metrics) <= 100
        
        # Test pagination
        response = await client.get(
            f"/api/v1/metrics/?device_id={device_id}&limit=50&skip=50", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        paged_metrics = response.json()
        assert len(paged_metrics) <= 50
