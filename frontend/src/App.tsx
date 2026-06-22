import React, { useState, useEffect, useCallback } from 'react';
import { authAPI } from './api/auth';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import AlertNotification from './components/AlertNotification';
import { useWebSocket } from './hooks/useWebSocket';
import { LogOut, Settings, Bell } from 'lucide-react';

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

const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [alerts, setAlerts] = useState<AlertData[]>([]);

  const handleAlert = useCallback((payload: { type: string; alert: AlertData }) => {
    if (payload.type === 'alert_created') {
      setAlerts((prev) => [payload.alert, ...prev].slice(0, 5));
    }
  }, []);

  useWebSocket(handleAlert);

  const dismissAlert = (id: number) => {
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  };

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      validateToken(token);
    } else {
      setLoading(false);
    }
  }, []);

  const validateToken = async (token: string) => {
    try {
      const userData = await authAPI.getCurrentUser();
      setUser(userData);
      setIsAuthenticated(true);
    } catch (error) {
      localStorage.removeItem('access_token');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = (token: string) => {
    setIsAuthenticated(true);
    validateToken(token);
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    setIsAuthenticated(false);
    setUser(null);
  };

  if (loading) {
    return (
      <div className="app-root app-center">
        <div className="spinner" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="app-root">
      <header className="app-header">
        <div className="app-header-inner">
          <div className="app-title">
            <div className="app-badge">HG</div>
            <h1>HomeGuard Monitor</h1>
          </div>

          <div className="app-actions">
            <button className="icon-btn" aria-label="Notifications">
              <Bell className="h-5 w-5" />
            </button>
            <button className="icon-btn" aria-label="Settings">
              <Settings className="h-5 w-5" />
            </button>
            <div className="user-chip">
              <span>{user?.full_name || user?.email}</span>
              <button onClick={handleLogout} className="icon-btn" title="Logout">
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="alert-container">
          {alerts.map((alert) => (
            <AlertNotification key={alert.id} alert={alert} onDismiss={dismissAlert} />
          ))}
        </div>
        <Dashboard />
      </main>
    </div>
  );
};

export default App;
