# HomeGuard Monitor Agents

This directory contains monitoring agents that collect system metrics and send them to the HomeGuard Monitor backend.

## System Monitoring Agent

The `monitoring_agent.py` script collects system metrics using `psutil` and sends them to the HomeGuard Monitor API.

### Installation

```bash
pip install -r requirements.txt
```

### Usage

#### Register a new device
```bash
python monitoring_agent.py --server http://localhost:8000 --register --name "My Server" --description "Main production server"
```

#### Start monitoring with existing device ID
```bash
python monitoring_agent.py --server http://localhost:8000 --device-id 1 --interval 30
```

#### Command line options
- `--server`: HomeGuard Monitor server URL (required)
- `--device-id`: Device ID if already registered
- `--name`: Device name (required for registration)
- `--description`: Device description (optional)
- `--device-type`: Type of device (server, iot_sensor, network_device, camera, other)
- `--interval`: Metrics collection interval in seconds (default: 30)
- `--register`: Register device before starting monitoring

### Collected Metrics

The agent collects the following metrics:

- **CPU**: Usage percentage
- **Memory**: Usage percentage and available bytes
- **Disk**: Usage percentage and free bytes
- **Network**: Bytes sent and received
- **Load Average**: 1-minute load average (Linux/Unix only)
- **Temperature**: Temperature sensor readings (if available)
- **Uptime**: System uptime in seconds
- **Process Count**: Number of running processes

### Platform Support

The agent supports:
- Linux
- Windows
- macOS

### Systemd Service (Linux)

Create a systemd service file:

```ini
# /etc/systemd/system/homeguard-agent.service
[Unit]
Description=HomeGuard Monitor Agent
After=network.target

[Service]
Type=simple
User=homeguard
WorkingDirectory=/opt/homeguard-agent
ExecStart=/opt/homeguard-agent/venv/bin/python monitoring_agent.py --server http://monitor-server:8000 --device-id 1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable homeguard-agent
sudo systemctl start homeguard-agent
```
