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
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const selectedDeviceData = devices.find(d => d.id === selectedDevice);
  const metricTypes = [...new Set(metrics.map(m => m.metric_type))];

  return (
    <div className="space-y-6">
      {/* Device Selection */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Device Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {devices.map(device => {
            const deviceStatus = getDeviceStatus(device);
            return (
              <div
                key={device.id}
                className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                  selectedDevice === device.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedDevice(device.id)}
              >
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">{device.name}</h3>
                  <span className={`text-sm ${deviceStatus.color}`}>
                    {deviceStatus.status}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1">{device.hostname}</p>
                <p className="text-xs text-gray-500 mt-1">{device.device_type}</p>
              </div>
            );
          })}
        </div>
      </div>

      {selectedDeviceData && (
        <>
          {/* Device Details */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Device Details</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Name</p>
                <p className="font-medium">{selectedDeviceData.name}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Hostname</p>
                <p className="font-medium">{selectedDeviceData.hostname}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">IP Address</p>
                <p className="font-medium">{selectedDeviceData.ip_address || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Type</p>
                <p className="font-medium">{selectedDeviceData.device_type}</p>
              </div>
            </div>
          </div>

          {/* Time Range Selection */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Metrics</h2>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(Number(e.target.value))}
                className="border border-gray-300 rounded px-3 py-1 text-sm"
              >
                <option value={1}>Last 1 hour</option>
                <option value={6}>Last 6 hours</option>
                <option value={24}>Last 24 hours</option>
                <option value={168}>Last 7 days</option>
              </select>
            </div>
          </div>

          {/* Metrics Charts */}
          <div className="space-y-6">
            {metricTypes.map(metricType => (
              <div key={metricType} className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center gap-2 mb-4">
                  {getMetricIcon(metricType)}
                  <h3 className="text-lg font-semibold capitalize">
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
