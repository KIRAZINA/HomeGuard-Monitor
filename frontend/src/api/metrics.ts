import api from './index';

export interface Metric {
  id: number;
  device_id: number;
  metric_type: string;
  value: number;
  unit?: string;
  tags?: Record<string, any>;
  timestamp: string;
}

export interface MetricCreate {
  device_id: number;
  metric_type: string;
  value: number;
  unit?: string;
  tags?: Record<string, any>;
  timestamp?: string;
}

export interface MetricQuery {
  device_id?: number;
  metric_type?: string;
  start_time: string;
  end_time: string;
  limit?: number;
}

export interface MetricSummary {
  device_id: number;
  metric_type: string;
  count: number;
  min_value: number;
  max_value: number;
  avg_value: number;
  latest_value: number;
  latest_timestamp: string;
}

export const metricsAPI = {
  getMetrics: async (query: MetricQuery): Promise<Metric[]> => {
    const params = new URLSearchParams();
    if (query.device_id) params.append('device_id', query.device_id.toString());
    if (query.metric_type) params.append('metric_type', query.metric_type);
    params.append('start_time', query.start_time);
    params.append('end_time', query.end_time);
    if (query.limit) params.append('limit', query.limit.toString());

    const response = await api.get(`/metrics?${params.toString()}`);
    return response.data;
  },

  getLatestMetrics: async (deviceId: number): Promise<Metric[]> => {
    const response = await api.get(`/metrics/device/${deviceId}/latest`);
    return response.data;
  },

  getMetricsSummary: async (deviceId: number, hours = 24): Promise<MetricSummary[]> => {
    const response = await api.get(`/metrics/device/${deviceId}/summary?hours=${hours}`);
    return response.data;
  },

  ingestMetrics: async (metrics: MetricCreate[]): Promise<void> => {
    await api.post('/metrics/ingest', metrics);
  },
};
