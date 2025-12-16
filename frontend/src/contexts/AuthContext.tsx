import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import api from '../services/api';

export enum Role {
  SYSTEM_ADMIN = 'system_admin',
  HR = 'hr',
  CAPABILITY_PARTNER = 'capability_partner',
  DELIVERY_MANAGER = 'delivery_manager',
  LINE_MANAGER = 'line_manager',
  EMPLOYEE = 'employee',
}

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
  capability?: string;
  employee_id: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  hasRole: (...roles: Role[]) => boolean;
  hasMinRoleLevel: (minLevel: number) => boolean;
}

const ROLE_LEVELS: Record<Role, number> = {
  [Role.SYSTEM_ADMIN]: 100,
  [Role.HR]: 90,
  [Role.CAPABILITY_PARTNER]: 70,
  [Role.DELIVERY_MANAGER]: 60,
  [Role.LINE_MANAGER]: 50,
  [Role.EMPLOYEE]: 10,
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await api.get('/api/auth/me');
      setUser(response.data);
    } catch {
      logout();
    }
  };

  const login = async (email: string, password: string) => {
    const response = await api.post('/api/auth/login', { email, password });
    const { access_token } = response.data;
    localStorage.setItem('token', access_token);
    setToken(access_token);
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    await fetchUser();
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete api.defaults.headers.common['Authorization'];
  };

  const hasRole = (...roles: Role[]) => user !== null && roles.includes(user.role);
  
  const hasMinRoleLevel = (minLevel: number) => 
    user !== null && ROLE_LEVELS[user.role] >= minLevel;

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!user, hasRole, hasMinRoleLevel }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
