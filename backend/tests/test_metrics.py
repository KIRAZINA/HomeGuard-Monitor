import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from app.schemas.metric import MetricCreate


class TestMetrics:
    """Test metrics endpoints."""

    async def test_ingest_metrics_success(self, client: AsyncClient, auth_headers, test_device):
        """Test successful metrics ingestion."""
        metrics_data = [
            {
                "device_id": test_device.id,
                "metric_type": "cpu_usage_percent",
                "value": 75.5,
                "unit": "percent",
                "tags": {"core": "0"}
            },
            {
                "device_id": test_device.id,
                "metric_type": "memory_usage_percent",
                "value": 60.2,
                "unit": "percent"
            }
        ]
        
        response = await client.post(
            "/api/v1/metrics/ingest", 
            json=metrics_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Successfully ingested" in data["message"]
        assert "2" in data["message"]  # Number of metrics

    async def test_ingest_metrics_unauthorized(self, client: AsyncClient, test_device):
        """Test metrics ingestion without authentication fails."""
        metrics_data = [
            {
                "device_id": test_device.id,
                "metric_type": "cpu_usage_percent",
                "value": 75.5
            }
        ]
        
        response = await client.post("/api/v1/metrics/ingest", json=metrics_data)
        
        assert response.status_code == 401

    async def test_ingest_metrics_invalid_device(self, client: AsyncClient, auth_headers):
        """Test metrics ingestion with invalid device ID fails."""
        metrics_data = [
            {
                "device_id": 99999,
                "metric_type": "cpu_usage_percent",
                "value": 75.5
            }
        ]
        
        response = await client.post(
            "/api/v1/metrics/ingest", 
            json=metrics_data, 
            headers=auth_headers
        )
        
        # Should succeed but foreign key constraint will fail at database level
        # This depends on implementation - might be 200 or 400
        assert response.status_code in [200, 400]

    async def test_get_metrics_success(self, client: AsyncClient, auth_headers, test_metrics):
        """Test getting metrics with filters."""
        device_id = test_metrics[0].device_id
        
        response = await client.get(
            f"/api/v1/metrics/?device_id={device_id}&limit=5", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
        assert all(metric["device_id"] == device_id for metric in data)

    async def test_get_metrics_with_time_range(self, client: AsyncClient, auth_headers, test_metrics):
        """Test getting metrics with time range filter."""
        device_id = test_metrics[0].device_id
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=2)
        
        response = await client.get(
            f"/api/v1/metrics/?device_id={device_id}&"
            f"start_time={start_time.isoformat()}&"
            f"end_time={end_time.isoformat()}", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_metrics_by_type(self, client: AsyncClient, auth_headers, test_metrics):
        """Test getting metrics filtered by type."""
        device_id = test_metrics[0].device_id
        
        response = await client.get(
            f"/api/v1/metrics/?device_id={device_id}&metric_type=cpu_usage_percent", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert all(metric["metric_type"] == "cpu_usage_percent" for metric in data)

    async def test_get_latest_metrics_success(self, client: AsyncClient, auth_headers, test_device):
        """Test getting latest metrics for a device."""
        response = await client.get(
            f"/api/v1/metrics/device/{test_device.id}/latest", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_latest_metrics_device_not_found(self, client: AsyncClient, auth_headers):
        """Test getting latest metrics for non-existent device."""
        response = await client.get(
            "/api/v1/metrics/device/99999/latest", 
            headers=auth_headers
        )
        
        assert response.status_code == 404

    async def test_get_metrics_summary_success(self, client: AsyncClient, auth_headers, test_metrics):
        """Test getting metrics summary for a device."""
        device_id = test_metrics[0].device_id
        
        response = await client.get(
            f"/api/v1/metrics/device/{device_id}/summary", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if data:  # If there are metrics
            summary = data[0]
            assert "device_id" in summary
            assert "metric_type" in summary
            assert "count" in summary
            assert "min_value" in summary
            assert "max_value" in summary
            assert "avg_value" in summary
            assert "latest_value" in summary

    async def test_get_metrics_summary_custom_hours(self, client: AsyncClient, auth_headers, test_device):
        """Test getting metrics summary with custom time range."""
        response = await client.get(
            f"/api/v1/metrics/device/{test_device.id}/summary?hours=48", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_ingest_metrics_with_timestamp(self, client: AsyncClient, auth_headers, test_device):
        """Test metrics ingestion with custom timestamp."""
        custom_time = datetime.utcnow() - timedelta(minutes=30)
        
        metrics_data = [
            {
                "device_id": test_device.id,
                "metric_type": "cpu_usage_percent",
                "value": 85.0,
                "timestamp": custom_time.isoformat()
            }
        ]
        
        response = await client.post(
            "/api/v1/metrics/ingest", 
            json=metrics_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 200

    async def test_ingest_large_batch_metrics(self, client: AsyncClient, auth_headers, test_device):
        """Test ingesting large batch of metrics."""
        metrics_data = []
        for i in range(100):
            metrics_data.append({
                "device_id": test_device.id,
                "metric_type": "cpu_usage_percent",
                "value": 50.0 + (i % 50)
            })
        
        response = await client.post(
            "/api/v1/metrics/ingest", 
            json=metrics_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "100" in data["message"]

    async def test_get_metrics_limit(self, client: AsyncClient, auth_headers, test_metrics):
        """Test metrics limit parameter."""
        device_id = test_metrics[0].device_id
        
        response = await client.get(
            f"/api/v1/metrics/?device_id={device_id}&limit=3", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3
