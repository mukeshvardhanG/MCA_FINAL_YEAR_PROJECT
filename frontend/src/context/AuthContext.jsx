import React, { createContext, useState, useEffect, useCallback, useContext } from 'react';
import {jwtDecode} from 'jwt-decode';
import api from '../services/api';

export const AuthContext = createContext();

export const useAuth = () => {
  return useContext(AuthContext);
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
      const decoded = jwtDecode(token);
      // Ensure student_id is available (mapping sub from JWT)
      const userObj = { 
        ...decoded, 
        student_id: decoded.sub, 
        name: localStorage.getItem('student_name'), 
        token 
      };
      return userObj;
    } catch (e) {
      localStorage.removeItem('token');
      return null;
    }
  }
  return null;
});
const [loading, setLoading] = useState(false);

useEffect(() => {
  setLoading(false);
}, []);

const login = useCallback(async (email, password) => {
  setLoading(true);
  try {
    const res = await api.post('/auth/login', { email, password });
    const { token, name, student_id } = res.data;
    localStorage.setItem('token', token);
    localStorage.setItem('student_name', name);
    
    const decoded = jwtDecode(token);
    setUser({ ...decoded, student_id: student_id || decoded.sub, name, token });
    return res.data;
  } finally {
    setLoading(false);
  }
}, []);

const register = useCallback(async (data) => {
  setLoading(true);
  try {
    const res = await api.post('/auth/register', data);
    const { token, name, student_id } = res.data;
    localStorage.setItem('token', token);
    localStorage.setItem('student_name', name);
    
    const decoded = jwtDecode(token);
    setUser({ ...decoded, student_id: student_id || decoded.sub, name, token });
    return res.data;
  } finally {
    setLoading(false);
  }
}, []);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('student_name');
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
