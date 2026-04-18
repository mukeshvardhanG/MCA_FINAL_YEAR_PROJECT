import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const studentId = localStorage.getItem('student_id');
    const name = localStorage.getItem('student_name');
    const role = localStorage.getItem('student_role') || 'student';
    if (token && studentId) {
      setUser({ student_id: studentId, name, token, role });
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    const { student_id, token, name, role } = res.data;
    localStorage.setItem('token', token);
    localStorage.setItem('student_id', student_id);
    localStorage.setItem('student_name', name);
    localStorage.setItem('student_role', role || 'student');
    setUser({ student_id, name, token, role: role || 'student' });
    return res.data;
  }, []);

  const register = useCallback(async (data) => {
    const res = await api.post('/auth/register', data);
    const { student_id, token, name, role } = res.data;
    localStorage.setItem('token', token);
    localStorage.setItem('student_id', student_id);
    localStorage.setItem('student_name', name);
    localStorage.setItem('student_role', role || 'student');
    setUser({ student_id, name, token, role: role || 'student' });
    return res.data;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('student_id');
    localStorage.removeItem('student_name');
    localStorage.removeItem('student_role');
    setUser(null);
  }, []);

  return { user, loading, login, register, logout };
}

