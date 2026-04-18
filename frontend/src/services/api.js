import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor — attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — handle 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('student_id');
      localStorage.removeItem('student_name');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// Admin API calls
export const getAdminStats = async () => {
  const response = await api.get('/dashboard/admin/stats');
  return response.data;
};

export default api;
