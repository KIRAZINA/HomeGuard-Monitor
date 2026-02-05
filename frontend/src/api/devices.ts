import api from './index';

export interface Device {
  id: number;
  name: string;
  description?: string;
  device_type: 'server' | 'iot_sensor' | 'network_device' | 'camera' | 'other';
  hostname: string;
  ip_address?: string;
  location?: string;
  tags?: string;
  status: 'online' | 'offline' | 'warning' | 'error';
  last_seen?: string;
  created_at: string;
  updated_at: string;
}

export interface DeviceCreate {
  name: string;
  description?: string;
  device_type: Device['device_type'];
  hostname: string;
  ip_address?: string;
  location?: string;
  tags?: string;
}

export const devicesAPI = {
  getDevices: async (skip = 0, limit = 100): Promise<Device[]> => {
    const response = await api.get(`/devices?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  getDevice: async (id: number): Promise<Device> => {
    const response = await api.get(`/devices/${id}`);
    return response.data;
  },

  createDevice: async (device: DeviceCreate): Promise<Device> => {
    const response = await api.post('/devices', device);
    return response.data;
  },

  updateDevice: async (id: number, device: Partial<DeviceCreate>): Promise<Device> => {
    const response = await api.put(`/devices/${id}`, device);
    return response.data;
  },

  deleteDevice: async (id: number): Promise<void> => {
    await api.delete(`/devices/${id}`);
  },
};
