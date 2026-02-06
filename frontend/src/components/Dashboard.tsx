import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { devicesAPI, metricsAPI, Device, Metric } from '../api';
import { Activity, Cpu, HardDrive, Network } from 'lucide-react';

interface DashboardProps {
  deviceId?: number;
}

const Dashboard: React.FC<DashboardProps> = ({ deviceId }) => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<number | undefined>(deviceId);
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(24); // hours
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [deviceForm, setDeviceForm] = useState({
    name: '',
    hostname: '',
    device_type: 'server' as Device['device_type'],
    ip_address: '',
    location: '',
    tags: '',
    description: ''
  });
  const [metricForm, setMetricForm] = useState({
    metric_type: 'cpu_usage_percent',
    value: '',
    unit: 'percent'
  });

  useEffect(() => {
    loadDevices();
  }, []);

  useEffect(() => {
    if (selectedDevice) {
      loadMetrics(selectedDevice, timeRange);
    }
  }, [selectedDevice, timeRange]);

  const loadDevices = async () => {
    try {
      const devicesData = await devicesAPI.getDevices();
      setDevices(devicesData);
      if (!selectedDevice && devicesData.length > 0) {
        setSelectedDevice(devicesData[0].id);
      }
    } catch (error) {
      console.error('Failed to load devices:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMetrics = async (deviceId: number, hours: number) => {
    try {
      const endTime = new Date().toISOString();
      const startTime = new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();
      
      const metricsData = await metricsAPI.getMetrics({
        device_id: deviceId,
        start_time: startTime,
        end_time: endTime,
        limit: 1000
      });
      
      setMetrics(metricsData);
    } catch (error) {
      console.error('Failed to load metrics:', error);
    }
  };

  const handleCreateDevice = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionMessage(null);
    if (!deviceForm.name || !deviceForm.hostname) {
      setActionMessage('Please provide at least name and hostname.');
      return;
    }

    try {
      const created = await devicesAPI.createDevice({
        name: deviceForm.name,
        hostname: deviceForm.hostname,
        device_type: deviceForm.device_type,
        description: deviceForm.description || undefined,
        ip_address: deviceForm.ip_address || undefined,
        location: deviceForm.location || undefined,
        tags: deviceForm.tags || undefined,
      });
      setActionMessage(`Device "${created.name}" created.`);
      setDeviceForm({
        name: '',
        hostname: '',
        device_type: 'server',
        ip_address: '',
        location: '',
        tags: '',
        description: ''
      });
      await loadDevices();
      setSelectedDevice(created.id);
    } catch (error) {
      console.error('Failed to create device:', error);
      setActionMessage('Failed to create device.');
    }
  };

  const handleIngestMetric = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionMessage(null);
    if (!selectedDevice) {
      setActionMessage('Select a device first.');
      return;
    }
    const value = Number(metricForm.value);
    if (Number.isNaN(value)) {
      setActionMessage('Metric value must be a number.');
      return;
    }

    try {
      await metricsAPI.ingestMetrics([
        {
          device_id: selectedDevice,
          metric_type: metricForm.metric_type,
          value,
          unit: metricForm.unit || undefined,
          timestamp: new Date().toISOString()
        }
      ]);
      setActionMessage('Metric ingested.');
      setMetricForm({ metric_type: metricForm.metric_type, value: '', unit: metricForm.unit });
      await loadMetrics(selectedDevice, timeRange);
    } catch (error) {
      console.error('Failed to ingest metric:', error);
      setActionMessage('Failed to ingest metric.');
    }
  };

  const getMetricIcon = (metricType: string) => {
    if (metricType.includes('cpu')) return <Cpu className="w-4 h-4" />;
    if (metricType.includes('disk')) return <HardDrive className="w-4 h-4" />;
    if (metricType.includes('network')) return <Network className="w-4 h-4" />;
    return <Activity className="w-4 h-4" />;
  };

  const formatChartData = (metricType: string) => {
    const filteredMetrics = metrics
      .filter(m => m.metric_type === metricType)
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
      .map(m => ({
        time: new Date(m.timestamp).toLocaleTimeString(),
        value: m.value,
        timestamp: m.timestamp
      }));

    return filteredMetrics;
  };

  const getDeviceStatus = (device: Device) => {
    const lastSeen = device.last_seen ? new Date(device.last_seen) : null;
    const now = new Date();
    const minutesAgo = lastSeen ? (now.getTime() - lastSeen.getTime()) / (1000 * 60) : Infinity;

    if (minutesAgo < 5) return { status: 'online', color: 'text-green-600' };
    if (minutesAgo < 15) return { status: 'warning', color: 'text-yellow-600' };
    return { status: 'offline', color: 'text-red-600' };
  };

  if (loading) {
    return (
      <div className="app-center" style={{ minHeight: 260 }}>
        <div className="spinner" />
      </div>
    );
  }

  const selectedDeviceData = devices.find(d => d.id === selectedDevice);
  const metricTypes = [...new Set(metrics.map(m => m.metric_type))];

  return (
    <div className="stack">
      {actionMessage && <div className="toast">{actionMessage}</div>}

      {/* Quick Actions */}
      <div className="panel accent-panel">
        <div className="panel-title">Quick Actions</div>
        <div className="two-col">
          <form className="form-card" onSubmit={handleCreateDevice}>
            <div className="form-title">Create Device</div>
            <label className="label">Name</label>
            <input
              className="input"
              value={deviceForm.name}
              onChange={(e) => setDeviceForm({ ...deviceForm, name: e.target.value })}
              placeholder="Home Server"
            />
            <label className="label">Hostname</label>
            <input
              className="input"
              value={deviceForm.hostname}
              onChange={(e) => setDeviceForm({ ...deviceForm, hostname: e.target.value })}
              placeholder="home-server"
            />
            <label className="label">Type</label>
            <select
              className="select"
              value={deviceForm.device_type}
              onChange={(e) => setDeviceForm({ ...deviceForm, device_type: e.target.value as Device['device_type'] })}
            >
              <option value="server">server</option>
              <option value="iot_sensor">iot_sensor</option>
              <option value="network_device">network_device</option>
              <option value="camera">camera</option>
              <option value="other">other</option>
            </select>
            <label className="label">IP Address</label>
            <input
              className="input"
              value={deviceForm.ip_address}
              onChange={(e) => setDeviceForm({ ...deviceForm, ip_address: e.target.value })}
              placeholder="192.168.1.10"
            />
            <label className="label">Location</label>
            <input
              className="input"
              value={deviceForm.location}
              onChange={(e) => setDeviceForm({ ...deviceForm, location: e.target.value })}
              placeholder="Living room"
            />
            <label className="label">Tags</label>
            <input
              className="input"
              value={deviceForm.tags}
              onChange={(e) => setDeviceForm({ ...deviceForm, tags: e.target.value })}
              placeholder="nas,backup"
            />
            <label className="label">Description</label>
            <input
              className="input"
              value={deviceForm.description}
              onChange={(e) => setDeviceForm({ ...deviceForm, description: e.target.value })}
              placeholder="Primary storage server"
            />
            <button className="btn btn-primary" type="submit">Create Device</button>
          </form>

          <form className="form-card" onSubmit={handleIngestMetric}>
            <div className="form-title">Ingest Metric</div>
            <label className="label">Device</label>
            <select
              className="select"
              value={selectedDevice ?? ''}
              onChange={(e) => setSelectedDevice(Number(e.target.value))}
            >
              <option value="" disabled>Select device</option>
              {devices.map((d) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
            <label className="label">Metric Type</label>
            <input
              className="input"
              value={metricForm.metric_type}
              onChange={(e) => setMetricForm({ ...metricForm, metric_type: e.target.value })}
              placeholder="cpu_usage_percent"
            />
            <label className="label">Value</label>
            <input
              className="input"
              value={metricForm.value}
              onChange={(e) => setMetricForm({ ...metricForm, value: e.target.value })}
              placeholder="72.5"
            />
            <label className="label">Unit</label>
            <input
              className="input"
              value={metricForm.unit}
              onChange={(e) => setMetricForm({ ...metricForm, unit: e.target.value })}
              placeholder="percent"
            />
            <button className="btn btn-secondary" type="submit">Send Metric</button>
          </form>
        </div>
      </div>

      {/* Device Selection */}
      <div className="panel">
        <h2 className="panel-title">Device Overview</h2>
        <div className="grid-cards">
          {devices.map(device => {
            const deviceStatus = getDeviceStatus(device);
            return (
              <div
                key={device.id}
                className={`card ${selectedDevice === device.id ? 'card-active' : ''}`}
                onClick={() => setSelectedDevice(device.id)}
              >
                <div className="card-row">
                  <h3>{device.name}</h3>
                  <span className={`status ${deviceStatus.status}`}>
                    {deviceStatus.status}
                  </span>
                </div>
                <p className="muted">{device.hostname}</p>
                <p className="tiny">{device.device_type}</p>
              </div>
            );
          })}
        </div>
      </div>

      {selectedDeviceData && (
        <>
          {/* Device Details */}
          <div className="panel">
            <h2 className="panel-title">Device Details</h2>
            <div className="detail-grid">
              <div>
                <p className="label">Name</p>
                <p className="value">{selectedDeviceData.name}</p>
              </div>
              <div>
                <p className="label">Hostname</p>
                <p className="value">{selectedDeviceData.hostname}</p>
              </div>
              <div>
                <p className="label">IP Address</p>
                <p className="value">{selectedDeviceData.ip_address || 'N/A'}</p>
              </div>
              <div>
                <p className="label">Type</p>
                <p className="value">{selectedDeviceData.device_type}</p>
              </div>
            </div>
          </div>

          {/* Time Range Selection */}
          <div className="panel">
            <div className="panel-row">
              <h2 className="panel-title">Metrics</h2>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(Number(e.target.value))}
                className="select"
              >
                <option value={1}>Last 1 hour</option>
                <option value={6}>Last 6 hours</option>
                <option value={24}>Last 24 hours</option>
                <option value={168}>Last 7 days</option>
              </select>
            </div>
          </div>

          {/* Metrics Charts */}
          <div className="stack">
            {metricTypes.map(metricType => (
              <div key={metricType} className="panel">
                <div className="panel-row">
                  {getMetricIcon(metricType)}
                  <h3 className="panel-title capitalize">
                    {metricType.replace(/_/g, ' ')}
                  </h3>
                </div>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={formatChartData(metricType)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="time" 
                      tick={{ fontSize: 12 }}
                      interval="preserveStartEnd"
                    />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip 
                      labelFormatter={(value) => `Time: ${value}`}
                      formatter={(value: any) => [value, 'Value']}
                    />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#3b82f6" 
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default Dashboard;
