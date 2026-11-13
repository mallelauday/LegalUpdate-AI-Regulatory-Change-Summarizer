import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('legalupdate_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('legalupdate_token') || null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const verifyUser = async () => {
      if (token) {
        try {
          const res = await api.get('/auth/me');
          if (res.data) {
            setUser(res.data);
            localStorage.setItem('legalupdate_user', JSON.stringify(res.data));
          }
        } catch (err) {
          console.warn('Session verification error:', err);
          logout();
        }
      }
      setLoading(false);
    };
    verifyUser();
  }, [token]);

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    if (res.success && res.data) {
      setToken(res.data.token);
      setUser(res.data.user);
      localStorage.setItem('legalupdate_token', res.data.token);
      localStorage.setItem('legalupdate_user', JSON.stringify(res.data.user));
      return res.data.user;
    }
    throw new Error(res.error || 'Login failed');
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('legalupdate_token');
    localStorage.removeItem('legalupdate_user');
  };

  const isAdmin = user?.role === 'admin';
  const isReviewer = user?.role === 'reviewer' || user?.role === 'admin';

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading, isAdmin, isReviewer }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

