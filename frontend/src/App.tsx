/** Main App component with routing. */
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { EmployeeDashboard } from './pages/EmployeeDashboard';
import { OnboardingMapSkills } from './pages/OnboardingMapSkills';
import { AdminUsers } from './pages/AdminUsers';
import { AdminDashboard } from './pages/AdminDashboard';
import { SkillGapBoard } from './pages/SkillGapBoard';
import { PrivateRoute } from './components/PrivateRoute';
import { authApi } from './services/api';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/dashboard"
          element={
            <PrivateRoute>
              <EmployeeDashboard />
            </PrivateRoute>
          }
        />
        <Route
          path="/onboarding"
          element={
            <PrivateRoute>
              <OnboardingMapSkills />
            </PrivateRoute>
          }
        />
        <Route
          path="/admin/users"
          element={
            <PrivateRoute>
              <AdminUsers />
            </PrivateRoute>
          }
        />
        <Route
          path="/admin/dashboard"
          element={
            <PrivateRoute>
              <AdminDashboard />
            </PrivateRoute>
          }
        />
        <Route
          path="/skill-gap"
          element={
            <PrivateRoute>
              <SkillGapBoard />
            </PrivateRoute>
          }
        />
        <Route
          path="/"
          element={(() => {
            const user = authApi.getUser();
            const to = user?.is_admin ? '/admin/dashboard' : '/dashboard';
            return <Navigate to={to} replace />;
          })()}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

