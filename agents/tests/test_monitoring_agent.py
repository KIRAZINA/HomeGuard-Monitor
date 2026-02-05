"""
Tests for the monitoring agent.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMonitoringAgent:
    """Test monitoring agent functionality."""

    @pytest.fixture
    def agent_config(self):
        """Create agent configuration."""
        return {
            "server_url": "http://localhost:8000",
            "device_id": 1,
            "interval": 30
        }

    def test_agent_initialization(self, agent_config):
        """Test agent initializes correctly."""
        from monitoring_agent import MonitoringAgent
        
        with patch('monitoring_agent.socket.socket'):
            agent = MonitoringAgent(
                server_url=agent_config["server_url"],
                device_id=agent_config["device_id"],
                interval=agent_config["interval"]
            )
            
            assert agent.server_url == "http://localhost:8000"
            assert agent.device_id == 1
            assert agent.interval == 30

    def test_get_local_ip(self, agent_config):
        """Test local IP address retrieval."""
        from monitoring_agent import MonitoringAgent
        
        with patch('monitoring_agent.socket.socket') as mock_socket:
            mock_socket_instance = MagicMock()
            mock_socket.return_value = mock_socket_instance
            mock_socket_instance.getsockname.return_value = ["192.168.1.100"]
            
            agent = MonitoringAgent(
                server_url=agent_config["server_url"],
                device_id=agent_config["device_id"],
                interval=agent_config["interval"]
            )
            
            ip = agent._get_local_ip()
            
            assert ip == "192.168.1.100"
            mock_socket_instance.connect.assert_called_once_with(("8.8.8.8", 80))
            mock_socket_instance.close.assert_called_once()

    def test_get_local_ip_fallback(self, agent_config):
        """Test local IP address fallback on error."""
        from monitoring_agent import MonitoringAgent
        
        with patch('monitoring_agent.socket.socket') as mock_socket:
            mock_socket.side_effect = Exception("Network error")
            
            agent = MonitoringAgent(
                server_url=agent_config["server_url"],
                device_id=agent_config["device_id"],
                interval=agent_config["interval"]
            )
            
            ip = agent._get_local_ip()
            
            assert ip == "127.0.0.1"

    @patch('monitoring_agent.psutil.cpu_percent')
    @patch('monitoring_agent.psutil.virtual_memory')
    @patch('monitoring_agent.psutil.disk_usage')
    @patch('monitoring_agent.psutil.net_io_counters')
    @patch('monitoring_agent.psutil.sensors_temperatures')
    @patch('monitoring_agent.psutil.boot_time')
    @patch('monitoring_agent.psutil.pids')
    def test_collect_system_metrics(self, mock_pids, mock_boot_time, 
                                    mock_temps, mock_net, mock_disk, 
                                    mock_memory, mock_cpu, agent_config):
        """Test system metrics collection."""
        from monitoring_agent import MonitoringAgent
        from datetime import datetime
        
        # Setup mocks
        mock_cpu.return_value = 75.5
        
        mock_memory.return_value = MagicMock(
            percent=60.0,
            available=8 * 1024**3  # 8 GB
        )
        
        mock_disk.return_value = MagicMock(
            used=500 * 1024**3,
            total=1000 * 1024**3,
            free=500 * 1024**3
        )
        
        mock_net.return_value = MagicMock(
            bytes_sent=1024 * 1024,
            bytes_recv=2048 * 1024
        )
        
        mock_temps.return_value = {}
        
        mock_boot_time.return_value = datetime.utcnow().timestamp() - 3600
        
        mock_pids.return_value = [1, 2, 3, 4, 5]
        
        agent = MonitoringAgent(
            server_url=agent_config["server_url"],
            device_id=agent_config["device_id"],
            interval=agent_config["interval"]
        )
        
        metrics = agent.collect_system_metrics()
        
        # Verify metrics were collected
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        
        # Check CPU metric
        cpu_metrics = [m for m in metrics if m["metric_type"] == "cpu_usage_percent"]
        assert len(cpu_metrics) == 1
        assert cpu_metrics[0]["value"] == 75.5

    @patch('monitoring_agent.psutil.cpu_percent')
    @patch('monitoring_agent.psutil.virtual_memory')
    @patch('monitoring_agent.psutil.disk_usage')
    @patch('monitoring_agent.psutil.net_io_counters')
    @patch('monitoring_agent.psutil.sensors_temperatures')
    @patch('monitoring_agent.psutil.boot_time')
    @patch('monitoring_agent.psutil.pids')
    def test_collect_metrics_with_temperature(self, mock_pids, mock_boot_time,
                                              mock_temps, mock_net,
                                              mock_disk, mock_memory, mock_cpu,
                                              agent_config):
        """Test metrics collection with temperature sensors."""
        from monitoring_agent import MonitoringAgent
        
        mock_cpu.return_value = 50.0
        mock_memory.return_value = MagicMock(percent=50.0, available=8 * 1024**3)
        mock_disk.return_value = MagicMock(used=100, total=1000, free=900)
        mock_net.return_value = MagicMock(bytes_sent=0, bytes_recv=0)
        
        mock_temps.return_value = {
            "cpu_thermal": [
                MagicMock(current=65.0, label="Package ID 0")
            ]
        }
        
        mock_boot_time.return_value = 0
        mock_pids.return_value = []
        
        agent = MonitoringAgent(
            server_url=agent_config["server_url"],
            device_id=agent_config["device_id"],
            interval=agent_config["interval"]
        )
        
        metrics = agent.collect_system_metrics()
        
        # Check for temperature metrics
        temp_metrics = [m for m in metrics if "temperature" in m["metric_type"]]
        assert len(temp_metrics) == 1
        assert temp_metrics[0]["value"] == 65.0
        assert temp_metrics[0]["unit"] == "celsius"

    @patch('monitoring_agent.requests.post')
    def test_send_metrics_success(self, mock_post, agent_config):
        """Test successful metrics sending."""
        from monitoring_agent import MonitoringAgent
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        agent = MonitoringAgent(
            server_url=agent_config["server_url"],
            device_id=agent_config["device_id"],
            interval=agent_config["interval"]
        )
        
        metrics = [
            {
                "device_id": 1,
                "metric_type": "cpu_usage_percent",
                "value": 75.5,
                "unit": "percent"
            }
        ]
        
        result = agent.send_metrics(metrics)
        
        assert result is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:8000/api/v1/metrics/ingest"
        assert call_args[1]["json"] == metrics

    @patch('monitoring_agent.requests.post')
    def test_send_metrics_failure(self, mock_post, agent_config):
        """Test metrics sending failure handling."""
        from monitoring_agent import MonitoringAgent
        import requests
        
        mock_post.side_effect = requests.exceptions.RequestException("Connection failed")
        
        agent = MonitoringAgent(
            server_url=agent_config["server_url"],
            device_id=agent_config["device_id"],
            interval=agent_config["interval"]
        )
        
        metrics = [{"device_id": 1, "metric_type": "cpu_usage_percent", "value": 75.5}]
        
        result = agent.send_metrics(metrics)
        
        assert result is False

    @patch('monitoring_agent.requests.post')
    def test_send_metrics_http_error(self, mock_post, agent_config):
        """Test metrics sending with HTTP error."""
        from monitoring_agent import MonitoringAgent
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        agent = MonitoringAgent(
            server_url=agent_config["server_url"],
            device_id=agent_config["device_id"],
            interval=agent_config["interval"]
        )
        
        metrics = [{"device_id": 1, "metric_type": "cpu_usage_percent", "value": 75.5}]
        
        result = agent.send_metrics(metrics)
        
        assert result is False

    @patch('monitoring_agent.requests.post')
    def test_register_device_success(self, mock_post, agent_config):
        """Test successful device registration."""
        from monitoring_agent import MonitoringAgent
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 5, "name": "Test Device"}
        mock_post.return_value = mock_response
        
        agent = MonitoringAgent(
            server_url=agent_config["server_url"],
            device_id=0,  # New device
            interval=agent_config["interval"]
        )
        
        result = agent.register_device(
            name="Test Device",
            description="A test device",
            device_type="server"
        )
        
        assert result is True
        assert agent.device_id == 5
        mock_post.assert_called_once()

    @patch('monitoring_agent.requests.post')
    def test_register_device_failure(self, mock_post, agent_config):
        """Test device registration failure."""
        from monitoring_agent import MonitoringAgent
        import requests
        
        mock_post.side_effect = requests.exceptions.RequestException("Connection failed")
        
        agent = MonitoringAgent(
            server_url=agent_config["server_url"],
            device_id=0,
            interval=agent_config["interval"]
        )
        
        result = agent.register_device(
            name="Test Device",
            description="A test device",
            device_type="server"
        )
        
        assert result is False


class TestMonitoringAgentCLI:
    """Test monitoring agent command line interface."""

    @patch('monitoring_agent.psutil')
    @patch('monitoring_agent.requests')
    def test_cli_parse_register(self, mock_requests, mock_psutil):
        """Test CLI registration argument parsing."""
        import sys
        from monitoring_agent import main
        from unittest.mock import MagicMock
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1}
        mock_requests.post.return_value = mock_response
        
        # Simulate registration
        test_args = [
            "monitoring_agent.py",
            "--server", "http://localhost:8000",
            "--register",
            "--name", "Test Server"
        ]
        
        with patch.object(sys, 'argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            # Should exit after successful registration
            assert exc_info.value.code == 0

    def test_cli_missing_required_args(self):
        """Test CLI with missing required arguments."""
        import sys
        from monitoring_agent import main
        from unittest.mock import patch
        
        test_args = ["monitoring_agent.py", "--server", "http://localhost:8000"]
        
        with patch.object(sys, 'argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            # Should fail due to missing device_id or register
            assert exc_info.value.code == 1

    def test_cli_register_requires_name(self):
        """Test that --register requires --name."""
        import sys
        from monitoring_agent import main
        from unittest.mock import patch
        
        test_args = [
            "monitoring_agent.py",
            "--server", "http://localhost:8000",
            "--register"
        ]
        
        with patch.object(sys, 'argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            # Should fail due to missing name
            assert exc_info.value.code == 1


class TestMonitoringAgentEdgeCases:
    """Test monitoring agent edge cases."""

    @pytest.fixture
    def agent_config(self):
        """Create agent configuration."""
        return {
            "server_url": "http://localhost:8000",
            "device_id": 1,
            "interval": 30
        }

    @patch('monitoring_agent.psutil')
    def test_collect_metrics_psutil_error(self, mock_psutil, agent_config):
        """Test metrics collection when psutil fails."""
        from monitoring_agent import MonitoringAgent
        
        mock_psutil.cpu_percent.side_effect = Exception("psutil error")
        
        agent = MonitoringAgent(
            server_url=agent_config["server_url"],
            device_id=agent_config["device_id"],
            interval=agent_config["interval"]
        )
        
        metrics = agent.collect_system_metrics()
        
        # Should return empty list on error
        assert metrics == []

    @patch('monitoring_agent.requests.post')
    def test_send_metrics_empty_list(self, mock_post, agent_config):
        """Test sending empty metrics list."""
        from monitoring_agent import MonitoringAgent
        
        agent = MonitoringAgent(
            server_url=agent_config["server_url"],
            device_id=agent_config["device_id"],
            interval=agent_config["interval"]
        )
        
        result = agent.send_metrics([])
        
        # Should handle empty list
        assert result is True
        mock_post.assert_not_called()

    def test_agent_url_trailing_slash(self, agent_config):
        """Test agent handles URL with trailing slash."""
        from monitoring_agent import MonitoringAgent
        
        with patch('monitoring_agent.socket.socket'):
            agent = MonitoringAgent(
                server_url="http://localhost:8000/",
                device_id=agent_config["device_id"],
                interval=agent_config["interval"]
            )
            
            # Should remove trailing slash
            assert agent.server_url == "http://localhost:8000"

    @patch('monitoring_agent.psutil')
    @patch('monitoring_agent.requests.post')
    def test_collect_metrics_tags(self, mock_post, mock_psutil, agent_config):
        """Test metrics collection with tags."""
        from monitoring_agent import MonitoringAgent
        
        mock_cpu = MagicMock()
        mock_cpu.return_value = 75.5
        mock_psutil.cpu_percent = mock_cpu
        
        mock_memory = MagicMock()
        mock_memory.return_value = MagicMock(percent=60.0, available=8 * 1024**3)
        mock_psutil.virtual_memory = mock_memory
        
        mock_disk = MagicMock()
        mock_disk.return_value = MagicMock(used=100, total=1000, free=900)
        mock_psutil.disk_usage = mock_disk
        
        mock_net = MagicMock()
        mock_net.return_value = MagicMock(bytes_sent=0, bytes_recv=0)
        mock_psutil.net_io_counters = mock_net
        
        mock_psutil.sensors_temperatures.return_value = {}
        mock_psutil.boot_time.return_value = 0
        mock_psutil.pids.return_value = []
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        agent = MonitoringAgent(
            server_url=agent_config["server_url"],
            device_id=agent_config["device_id"],
            interval=agent_config["interval"]
        )
        
        metrics = agent.collect_system_metrics()
        
        # Verify metrics have required fields
        for metric in metrics:
            assert "device_id" in metric
            assert "metric_type" in metric
            assert "value" in metric
            assert "timestamp" in metric
            assert "unit" in metric
