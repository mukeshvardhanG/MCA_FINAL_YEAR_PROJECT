import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import PublicProfilePage from './pages/PublicProfilePage';
import AdminDashboard from './pages/AdminDashboard';
import TeacherPortal from './pages/TeacherPortal';
import ProtectedRoute from './components/ProtectedRoute';

function RoleRedirect() {
  const { user } = useAuth();
  const role = user?.role || 'student';
  if (role === 'admin') return <Navigate to="/admin" />;
  if (role === 'teacher') return <Navigate to="/teacher" />;
  return <Navigate to="/dashboard" />;
}

function App() {
  const { user, loading, login, register, logout } = useAuth();

  if (loading) {
    return (
      <div className="loading-overlay">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <Routes>
      <Route
        path="/"
        element={
          user ? (
            <RoleRedirect />
          ) : (
            <LoginPage onLogin={login} onRegister={register} />
          )
        }
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute allowedRoles={['student']}>
            <DashboardPage user={user} onLogout={logout} />
          </ProtectedRoute>
        }
      />
      <Route
        path="/teacher/*"
        element={
          <ProtectedRoute allowedRoles={['teacher', 'admin']}>
            <TeacherPortal user={user} onLogout={logout} />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/*"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminDashboard user={user} onLogout={logout} />
          </ProtectedRoute>
        }
      />
      <Route path="/profile/:studentId" element={<PublicProfilePage />} />
    </Routes>
  );
}

export default App;
