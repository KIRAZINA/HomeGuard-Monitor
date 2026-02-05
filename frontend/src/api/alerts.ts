import api from './index';

export interface AlertRule {
  id: number;
  name: string;
  description?: string;
  device_id?: number;
  metric_type: string;
  rule_type: 'threshold' | 'anomaly';
  severity: 'info' | 'warning' | 'critical';
  threshold_value?: number;
  comparison_operator?: 'gt' | 'lt' | 'gte' | 'lte' | 'eq' | 'ne';
  evaluation_window_minutes: number;
  notification_channels: ('email' | 'telegram' | 'discord' | 'sms')[];
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface AlertRuleCreate {
  name: string;
  description?: string;
  device_id?: number;
  metric_type: string;
  rule_type: AlertRule['rule_type'];
  severity: AlertRule['severity'];
  threshold_value?: number;
  comparison_operator?: AlertRule['comparison_operator'];
  evaluation_window_minutes?: number;
  notification_channels?: AlertRule['notification_channels'];
  enabled?: boolean;
}

export interface Alert {
  id: number;
  rule_id: number;
  device_id: number;
  metric_type: string;
  severity: AlertRule['severity'];
  status: 'active' | 'acknowledged' | 'resolved' | 'snoozed';
  message: string;
  trigger_value: number;
  triggered_at: string;
  acknowledged_at?: string;
  acknowledged_by?: string;
  resolved_at?: string;
  snoozed_until?: string;
}

export const alertsAPI = {
  getAlertRules: async (skip = 0, limit = 100): Promise<AlertRule[]> => {
    const response = await api.get(`/alerts/rules?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  createAlertRule: async (rule: AlertRuleCreate): Promise<AlertRule> => {
    const response = await api.post('/alerts/rules', rule);
    return response.data;
  },

  updateAlertRule: async (id: number, rule: Partial<AlertRuleCreate>): Promise<AlertRule> => {
    const response = await api.put(`/alerts/rules/${id}`, rule);
    return response.data;
  },

  deleteAlertRule: async (id: number): Promise<void> => {
    await api.delete(`/alerts/rules/${id}`);
  },

  getAlerts: async (skip = 0, limit = 100, acknowledged?: boolean): Promise<Alert[]> => {
    const params = new URLSearchParams();
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    if (acknowledged !== undefined) {
      params.append('acknowledged', acknowledged.toString());
    }

    const response = await api.get(`/alerts?${params.toString()}`);
    return response.data;
  },

  acknowledgeAlert: async (id: number): Promise<void> => {
    await api.post(`/alerts/${id}/acknowledge`);
  },

  snoozeAlert: async (id: number, minutes = 30): Promise<void> => {
    await api.post(`/alerts/${id}/snooze?minutes=${minutes}`);
  },
};
