import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth, Role } from '../contexts/AuthContext';
import { RoleVisible, useRoleAccess } from '../components/RoleGuard';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const { isAdmin, isHR, isManager, isCP, canViewSensitive } = useRoleAccess();

  const roleLabels: Record<Role, string> = {
    [Role.SYSTEM_ADMIN]: 'System Administrator',
    [Role.HR]: 'Human Resources',
    [Role.CAPABILITY_PARTNER]: 'Capability Partner',
    [Role.DELIVERY_MANAGER]: 'Delivery Manager',
    [Role.LINE_MANAGER]: 'Line Manager',
    [Role.EMPLOYEE]: 'Employee',
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">Welcome, {user?.first_name}!</h1>
      <p className="text-gray-600 mb-6">Role: {user?.role && roleLabels[user.role]}</p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* All users */}
        <DashboardCard title="My Profile" description="View and edit your profile" link="/profile" />
        <DashboardCard title="My Skills" description="Manage your skills" link="/skills" />

        {/* HR & Admin */}
        <RoleVisible roles={[Role.SYSTEM_ADMIN, Role.HR]}>
          <DashboardCard title="All Employees" description="View all employee data" link="/employees" highlight />
          <DashboardCard title="Audit Logs" description="View sensitive data access logs" link="/admin/audit-logs" />
        </RoleVisible>

        {/* Admin only */}
        <RoleVisible roles={[Role.SYSTEM_ADMIN]}>
          <DashboardCard title="User Management" description="Manage system users" link="/admin/users" highlight />
        </RoleVisible>

        {/* Managers */}
        <RoleVisible roles={[Role.LINE_MANAGER, Role.DELIVERY_MANAGER]}>
          <DashboardCard title="My Reports" description="View your direct reports" link="/my-reports" />
        </RoleVisible>

        {/* Capability Partner */}
        <RoleVisible roles={[Role.CAPABILITY_PARTNER]}>
          <DashboardCard title="Capability View" description={`View ${user?.capability} employees`} link="/capability" />
          <DashboardCard title="Capability Metrics" description="Aggregate skill metrics" link="/capability/metrics" />
        </RoleVisible>

        {/* CP, DM, HR, Admin - Metrics */}
        <RoleVisible roles={[Role.CAPABILITY_PARTNER, Role.DELIVERY_MANAGER, Role.HR, Role.SYSTEM_ADMIN]}>
          <DashboardCard title="Skill Analytics" description="View aggregate metrics" link="/capability/metrics" />
        </RoleVisible>
      </div>

      {/* Role-specific notices */}
      {canViewSensitive && (
        <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded">
          <p className="text-yellow-800 text-sm">
            ⚠️ You have access to sensitive employee data. All access is logged for GDPR compliance.
          </p>
        </div>
      )}
    </div>
  );
};

const DashboardCard: React.FC<{ title: string; description: string; link: string; highlight?: boolean }> = ({
  title, description, link, highlight
}) => (
  <Link to={link} className={`block p-4 rounded-lg border transition-shadow hover:shadow-md ${highlight ? 'bg-blue-50 border-blue-200' : 'bg-white border-gray-200'}`}>
    <h3 className="font-semibold text-lg">{title}</h3>
    <p className="text-gray-600 text-sm">{description}</p>
  </Link>
);

export default Dashboard;
