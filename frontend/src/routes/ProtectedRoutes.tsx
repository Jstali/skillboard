import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { RoleGuard } from '../components/RoleGuard';
import { Role } from '../contexts/AuthContext';

// Page imports (create these components)
import Dashboard from '../pages/Dashboard';
import MyProfile from '../pages/MyProfile';
import EmployeeList from '../pages/EmployeeList';
import EmployeeDetail from '../pages/EmployeeDetail';
import MyReports from '../pages/MyReports';
import CapabilityView from '../pages/CapabilityView';
import CapabilityMetrics from '../pages/CapabilityMetrics';
import AuditLogs from '../pages/AuditLogs';
import UserManagement from '../pages/UserManagement';
import Login from '../pages/Login';

const ProtectedRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<Login />} />
      
      {/* All authenticated users */}
      <Route path="/dashboard" element={
        <RoleGuard><Dashboard /></RoleGuard>
      } />
      <Route path="/profile" element={
        <RoleGuard><MyProfile /></RoleGuard>
      } />
      
      {/* HR & Admin - Full employee access */}
      <Route path="/employees" element={
        <RoleGuard allowedRoles={[Role.SYSTEM_ADMIN, Role.HR]} redirectTo="/dashboard">
          <EmployeeList />
        </RoleGuard>
      } />
      <Route path="/employees/:id" element={
        <RoleGuard allowedRoles={[Role.SYSTEM_ADMIN, Role.HR, Role.LINE_MANAGER, Role.DELIVERY_MANAGER, Role.CAPABILITY_PARTNER]}>
          <EmployeeDetail />
        </RoleGuard>
      } />
      
      {/* Managers - Direct reports */}
      <Route path="/my-reports" element={
        <RoleGuard allowedRoles={[Role.LINE_MANAGER, Role.DELIVERY_MANAGER, Role.HR, Role.SYSTEM_ADMIN]} redirectTo="/dashboard">
          <MyReports />
        </RoleGuard>
      } />
      
      {/* Capability Partner - Capability view */}
      <Route path="/capability" element={
        <RoleGuard allowedRoles={[Role.CAPABILITY_PARTNER, Role.HR, Role.SYSTEM_ADMIN]} redirectTo="/dashboard">
          <CapabilityView />
        </RoleGuard>
      } />
      <Route path="/capability/metrics" element={
        <RoleGuard allowedRoles={[Role.CAPABILITY_PARTNER, Role.DELIVERY_MANAGER, Role.HR, Role.SYSTEM_ADMIN]} redirectTo="/dashboard">
          <CapabilityMetrics />
        </RoleGuard>
      } />
      
      {/* Admin only */}
      <Route path="/admin/users" element={
        <RoleGuard allowedRoles={[Role.SYSTEM_ADMIN]} redirectTo="/dashboard">
          <UserManagement />
        </RoleGuard>
      } />
      <Route path="/admin/audit-logs" element={
        <RoleGuard allowedRoles={[Role.SYSTEM_ADMIN, Role.HR]} redirectTo="/dashboard">
          <AuditLogs />
        </RoleGuard>
      } />
      
      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

export default ProtectedRoutes;
