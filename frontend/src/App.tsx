import React, { useState, useEffect } from 'react';
import { authAPI } from './api/auth';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import { LogOut, Settings, Bell } from 'lucide-react';

const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

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
        <Dashboard />
      </main>
    </div>
  );
};

export default App;
