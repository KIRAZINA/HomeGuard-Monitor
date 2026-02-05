#!/usr/bin/env python3
"""
HomeGuard Monitor - Monitoring Agent

This agent collects system metrics and sends them to the HomeGuard Monitor backend.
It supports Linux, Windows, and macOS.
"""

import psutil
import platform
import socket
import time
import json
import argparse
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional
import sys


class MonitoringAgent:
    def __init__(self, server_url: str, device_id: int, interval: int = 30):
        self.server_url = server_url.rstrip('/')
        self.device_id = device_id
        self.interval = interval
        self.hostname = socket.gethostname()
        self.ip_address = self._get_local_ip()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _get_local_ip(self) -> str:
        """Get local IP address"""
        try:
            # Create a socket to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def collect_system_metrics(self) -> List[Dict]:
        """Collect system metrics"""
        metrics = []
        timestamp = datetime.utcnow().isoformat()

        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append({
                "device_id": self.device_id,
                "metric_type": "cpu_usage_percent",
                "value": cpu_percent,
                "unit": "percent",
                "timestamp": timestamp
            })

            # Memory metrics
            memory = psutil.virtual_memory()
            metrics.append({
                "device_id": self.device_id,
                "metric_type": "memory_usage_percent",
                "value": memory.percent,
                "unit": "percent",
                "timestamp": timestamp
            })
            metrics.append({
                "device_id": self.device_id,
                "metric_type": "memory_available_bytes",
                "value": memory.available,
                "unit": "bytes",
                "timestamp": timestamp
            })

            # Disk metrics
            disk_usage = psutil.disk_usage('/')
            metrics.append({
                "device_id": self.device_id,
                "metric_type": "disk_usage_percent",
                "value": (disk_usage.used / disk_usage.total) * 100,
                "unit": "percent",
                "timestamp": timestamp
            })
            metrics.append({
                "device_id": self.device_id,
                "metric_type": "disk_free_bytes",
                "value": disk_usage.free,
                "unit": "bytes",
                "timestamp": timestamp
            })

            # Network metrics
            network_io = psutil.net_io_counters()
            metrics.append({
                "device_id": self.device_id,
                "metric_type": "network_bytes_sent",
                "value": network_io.bytes_sent,
                "unit": "bytes",
                "timestamp": timestamp
            })
            metrics.append({
                "device_id": self.device_id,
                "metric_type": "network_bytes_recv",
                "value": network_io.bytes_recv,
                "unit": "bytes",
                "timestamp": timestamp
            })

            # Load average (Linux/Unix only)
            if hasattr(psutil, 'getloadavg'):
                load_avg = psutil.getloadavg()
                metrics.append({
                    "device_id": self.device_id,
                    "metric_type": "load_average_1m",
                    "value": load_avg[0],
                    "unit": "load",
                    "timestamp": timestamp
                })

            # Temperature sensors (if available)
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        for entry in entries:
                            metrics.append({
                                "device_id": self.device_id,
                                "metric_type": f"temperature_{name.lower()}",
                                "value": entry.current,
                                "unit": "celsius",
                                "timestamp": timestamp,
                                "tags": {"sensor": entry.label or name}
                            })
            except AttributeError:
                pass  # Temperature sensors not available

            # Boot time
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            metrics.append({
                "device_id": self.device_id,
                "metric_type": "uptime_seconds",
                "value": uptime,
                "unit": "seconds",
                "timestamp": timestamp
            })

            # Process count
            process_count = len(psutil.pids())
            metrics.append({
                "device_id": self.device_id,
                "metric_type": "process_count",
                "value": process_count,
                "unit": "count",
                "timestamp": timestamp
            })

        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")

        return metrics

    def send_metrics(self, metrics: List[Dict]) -> bool:
        """Send metrics to the server"""
        try:
            url = f"{self.server_url}/api/v1/metrics/ingest"
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, json=metrics, headers=headers, timeout=10)
            
            if response.status_code == 200:
                self.logger.debug(f"Successfully sent {len(metrics)} metrics")
                return True
            else:
                self.logger.error(f"Failed to send metrics: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error sending metrics: {e}")
            return False

    def register_device(self, name: str, description: str = "", device_type: str = "server") -> bool:
        """Register this device with the server"""
        try:
            url = f"{self.server_url}/api/v1/devices/"
            device_data = {
                "name": name,
                "description": description,
                "device_type": device_type,
                "hostname": self.hostname,
                "ip_address": self.ip_address,
                "location": platform.platform()
            }
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, json=device_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                device_info = response.json()
                self.device_id = device_info["id"]
                self.logger.info(f"Device registered successfully with ID: {self.device_id}")
                return True
            else:
                self.logger.error(f"Failed to register device: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error registering device: {e}")
            return False

    def run(self):
        """Main monitoring loop"""
        self.logger.info(f"Starting monitoring agent for device {self.device_id}")
        self.logger.info(f"Collecting metrics every {self.interval} seconds")
        
        while True:
            try:
                # Collect metrics
                metrics = self.collect_system_metrics()
                
                if metrics:
                    # Send metrics to server
                    success = self.send_metrics(metrics)
                    if success:
                        self.logger.debug(f"Sent {len(metrics)} metrics to server")
                    else:
                        self.logger.warning("Failed to send metrics to server")
                
                # Wait for next interval
                time.sleep(self.interval)
                
            except KeyboardInterrupt:
                self.logger.info("Monitoring agent stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in monitoring loop: {e}")
                time.sleep(self.interval)


def main():
    parser = argparse.ArgumentParser(description="HomeGuard Monitor Agent")
    parser.add_argument("--server", required=True, help="HomeGuard Monitor server URL")
    parser.add_argument("--device-id", type=int, help="Device ID (if already registered)")
    parser.add_argument("--name", help="Device name (for registration)")
    parser.add_argument("--description", default="", help="Device description")
    parser.add_argument("--device-type", default="server", 
                       choices=["server", "iot_sensor", "network_device", "camera", "other"],
                       help="Device type")
    parser.add_argument("--interval", type=int, default=30, 
                       help="Metrics collection interval in seconds")
    parser.add_argument("--register", action="store_true", 
                       help="Register device before starting monitoring")
    
    args = parser.parse_args()
    
    if args.register and not args.name:
        print("Error: --name is required when using --register")
        sys.exit(1)
    
    if not args.device_id and not args.register:
        print("Error: Either --device-id or --register must be specified")
        sys.exit(1)
    
    # Create monitoring agent
    agent = MonitoringAgent(args.server, args.device_id or 0, args.interval)
    
    # Register device if requested
    if args.register:
        if not agent.register_device(args.name, args.description, args.device_type):
            print("Failed to register device")
            sys.exit(1)
    
    # Start monitoring
    agent.run()


if __name__ == "__main__":
    main()
