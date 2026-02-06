import React, { useState } from 'react';
import { authAPI, LoginCredentials, RegisterData } from '../api';
import { Eye, EyeOff, LogIn, UserPlus } from 'lucide-react';

interface LoginProps {
  onLogin: (token: string) => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    email: '',
    full_name: '',
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (isLogin) {
        const credentials: LoginCredentials = {
          username: formData.username,
          password: formData.password,
        };
        const response = await authAPI.login(credentials);
        localStorage.setItem('access_token', response.access_token);
        onLogin(response.access_token);
      } else {
        const registerData: RegisterData = {
          email: formData.email,
          password: formData.password,
          full_name: formData.full_name,
        };
        await authAPI.register(registerData);
        // After successful registration, log in
        const credentials: LoginCredentials = {
          username: formData.email,
          password: formData.password,
        };
        const response = await authAPI.login(credentials);
        localStorage.setItem('access_token', response.access_token);
        onLogin(response.access_token);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-root">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-badge">HG</div>
          <h2>HomeGuard Monitor</h2>
          <p>{isLogin ? 'Sign in to your account' : 'Create a new account'}</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {error && (
            <div className="auth-error">
              {error}
            </div>
          )}
          
          <div className="auth-grid">
            {!isLogin && (
              <>
                <div>
                  <label htmlFor="full_name" className="label">Full Name</label>
                  <input
                    id="full_name"
                    name="full_name"
                    type="text"
                    value={formData.full_name}
                    onChange={handleInputChange}
                    className="input"
                  />
                </div>
                
                <div>
                  <label htmlFor="email" className="label">Email</label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    required={!isLogin}
                    className="input"
                  />
                </div>
              </>
            )}
            
            <div>
              <label htmlFor="username" className="label">{isLogin ? 'Email or Username' : 'Username'}</label>
              <input
                id="username"
                name="username"
                type="text"
                value={formData.username}
                onChange={handleInputChange}
                required
                className="input"
              />
            </div>
            
            <div>
              <label htmlFor="password" className="label">Password</label>
              <div className="password-field">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={handleInputChange}
                  required
                  className="input"
                />
                <button
                  type="button"
                  className="icon-btn auth-eye"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>
          </div>

          <button type="submit" disabled={loading} className="btn btn-primary auth-submit">
            {loading ? (
              <div className="spinner-sm" />
            ) : (
              <>
                {isLogin ? (
                  <>
                    <LogIn className="h-4 w-4" />
                    Sign in
                  </>
                ) : (
                  <>
                    <UserPlus className="h-4 w-4" />
                    Sign up
                  </>
                )}
              </>
            )}
          </button>

          <div className="auth-switch">
            <button
              type="button"
              onClick={() => {
                setIsLogin(!isLogin);
                setError('');
              }}
              className="link-btn"
            >
              {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;
