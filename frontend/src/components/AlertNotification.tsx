import React from 'react';
import { AlertTriangle, X } from 'lucide-react';

interface AlertData {
  id: number;
  rule_id: number;
  device_id: number;
  metric_type: string;
  severity: string;
  message: string;
  trigger_value: number;
  triggered_at: string;
}

interface AlertNotificationProps {
  alert: AlertData;
  onDismiss: (id: number) => void;
}

const severityColors: Record<string, string> = {
  critical: 'bg-red-100 border-red-500 text-red-800',
  warning: 'bg-yellow-100 border-yellow-500 text-yellow-800',
  info: 'bg-blue-100 border-blue-500 text-blue-800',
};

const AlertNotification: React.FC<AlertNotificationProps> = ({ alert, onDismiss }) => {
  const colorClass = severityColors[alert.severity] || severityColors.info;

  return (
    <div className={`alert-toast ${colorClass}`}>
      <div className="alert-toast-icon">
        <AlertTriangle className="w-5 h-5" />
      </div>
      <div className="alert-toast-body">
        <div className="alert-toast-severity">{alert.severity.toUpperCase()}</div>
        <div className="alert-toast-message">{alert.message}</div>
        <div className="alert-toast-meta">
          device #{alert.device_id} &middot; {alert.metric_type} &middot; {alert.trigger_value}
        </div>
      </div>
      <button className="alert-toast-close" onClick={() => onDismiss(alert.id)}>
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};

export default AlertNotification;
