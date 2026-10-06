/**
 * auth.js – React context + hook for global authentication state.
 *
 * Stores the JWT token and user info in localStorage so the session
 * survives page refreshes.
 */

import { createContext, useContext, useState, useCallback } from 'react';
import api from './api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  /** Persist user info + token returned by signup / login */
  const login = useCallback((userData) => {
    const { token, ...rest } = userData;
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(rest));
    setUser(rest);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  }, []);

  /** POST /auth/signup */
  const signup = useCallback(async (username, email, password) => {
    const { data, error } = await api.post('/auth/signup', { username, email, password });
    if (error) return { error };
    login(data);
    return { data };
  }, [login]);

  /** POST /auth/login */
  const loginWithCredentials = useCallback(async (email, password) => {
    const { data, error } = await api.post('/auth/login', { email, password });
    if (error) return { error };
    login(data);
    return { data };
  }, [login]);

  return (
    <AuthContext.Provider value={{ user, login, logout, signup, loginWithCredentials }}>
      {children}
    </AuthContext.Provider>
  );
}

/** Custom hook – throws if used outside <AuthProvider /> */
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>');
  return ctx;
}
