import pytest
from httpx import AsyncClient
from app.schemas.device import DeviceCreate, DeviceUpdate
from app.models.device import DeviceType, DeviceStatus


class TestDevices:
    """Test device management endpoints."""

    async def test_create_device_success(self, client: AsyncClient, auth_headers):
        """Test successful device creation."""
        device_data = {
            "name": "Test Server",
            "description": "A test server for monitoring",
            "device_type": "server",
            "hostname": "test-server.local",
            "ip_address": "192.168.1.100",
            "location": "Home Lab",
            "tags": "test,server"
        }
        
        response = await client.post(
            "/api/v1/devices/", 
            json=device_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == device_data["name"]
        assert data["hostname"] == device_data["hostname"]
        assert data["device_type"] == device_data["device_type"]
        assert data["status"] == "offline"  # Default status
        assert "id" in data
        assert "created_at" in data

    async def test_create_device_unauthorized(self, client: AsyncClient):
        """Test device creation without authentication fails."""
        device_data = {
            "name": "Test Server",
            "device_type": "server",
            "hostname": "test-server.local"
        }
        
        response = await client.post("/api/v1/devices/", json=device_data)
        
        assert response.status_code == 401

    async def test_create_device_invalid_data(self, client: AsyncClient, auth_headers):
        """Test device creation with invalid data fails."""
        device_data = {
            "name": "",  # Empty name should fail
            "device_type": "server",
            "hostname": "test-server.local"
        }
        
        response = await client.post(
            "/api/v1/devices/", 
            json=device_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 422

    async def test_get_devices_success(self, client: AsyncClient, auth_headers, test_device):
        """Test getting list of devices."""
        response = await client.get("/api/v1/devices/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(device["id"] == test_device.id for device in data)

    async def test_get_device_success(self, client: AsyncClient, auth_headers, test_device):
        """Test getting a specific device."""
        response = await client.get(
            f"/api/v1/devices/{test_device.id}", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_device.id
        assert data["name"] == test_device.name

    async def test_get_device_not_found(self, client: AsyncClient, auth_headers):
        """Test getting non-existent device fails."""
        response = await client.get("/api/v1/devices/99999", headers=auth_headers)
        
        assert response.status_code == 404
        assert "Device not found" in response.json()["detail"]

    async def test_update_device_success(self, client: AsyncClient, auth_headers, test_device):
        """Test successful device update."""
        update_data = {
            "name": "Updated Server Name",
            "description": "Updated description",
            "location": "New Location"
        }
        
        response = await client.put(
            f"/api/v1/devices/{test_device.id}", 
            json=update_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["location"] == update_data["location"]
        assert data["hostname"] == test_device.hostname  # Unchanged

    async def test_update_device_not_found(self, client: AsyncClient, auth_headers):
        """Test updating non-existent device fails."""
        update_data = {"name": "Updated Name"}
        
        response = await client.put(
            "/api/v1/devices/99999", 
            json=update_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 404

    async def test_delete_device_success(self, client: AsyncClient, auth_headers, test_device):
        """Test successful device deletion."""
        response = await client.delete(
            f"/api/v1/devices/{test_device.id}", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]

        # Verify device is deleted
        get_response = await client.get(
            f"/api/v1/devices/{test_device.id}", 
            headers=auth_headers
        )
        assert get_response.status_code == 404

    async def test_delete_device_not_found(self, client: AsyncClient, auth_headers):
        """Test deleting non-existent device fails."""
        response = await client.delete("/api/v1/devices/99999", headers=auth_headers)
        
        assert response.status_code == 404

    async def test_device_types_validation(self, client: AsyncClient, auth_headers):
        """Test device type validation."""
        valid_types = ["server", "iot_sensor", "network_device", "camera", "other"]
        
        for device_type in valid_types:
            device_data = {
                "name": f"Test {device_type}",
                "device_type": device_type,
                "hostname": f"test-{device_type}.local"
            }
            
            response = await client.post(
                "/api/v1/devices/", 
                json=device_data, 
                headers=auth_headers
            )
            
            assert response.status_code == 200

    async def test_device_invalid_type(self, client: AsyncClient, auth_headers):
        """Test invalid device type fails."""
        device_data = {
            "name": "Test Device",
            "device_type": "invalid_type",
            "hostname": "test.local"
        }
        
        response = await client.post(
            "/api/v1/devices/", 
            json=device_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 422
