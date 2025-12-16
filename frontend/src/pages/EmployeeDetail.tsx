import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../services/api';
import { useAuth, Role } from '../contexts/AuthContext';
import { useRoleAccess } from '../components/RoleGuard';

interface Employee {
  id: number;
  employee_id: string;
  first_name: string;
  last_name: string;
  email: string;
  department?: string;
  capability?: string;
  role: string;
  joining_date?: string;
  // Sensitive - may be masked
  personal_email?: string;
  phone_number?: string;
  salary?: number | string;
  performance_rating?: string;
}

const EmployeeDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const { canViewSensitive } = useRoleAccess();
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEmployee = async () => {
      try {
        const response = await api.get(`/api/v2/employees/${id}`);
        setEmployee(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Access denied');
      } finally {
        setLoading(false);
      }
    };
    fetchEmployee();
  }, [id]);

  if (loading) return <div className="p-6">Loading...</div>;
  if (error) return <div className="p-6 text-red-600">{error}</div>;
  if (!employee) return <div className="p-6">Employee not found</div>;

  const isSelf = user?.id === employee.id;
  const isMasked = (value: any) => value === '***REDACTED***';

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">
        {employee.first_name} {employee.last_name}
        {isSelf && <span className="ml-2 text-sm text-blue-600">(You)</span>}
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Basic Info - All can see */}
        <Section title="Basic Information">
          <Field label="Employee ID" value={employee.employee_id} />
          <Field label="Email" value={employee.email} />
          <Field label="Department" value={employee.department} />
          <Field label="Capability" value={employee.capability} />
          <Field label="Role" value={employee.role} />
        </Section>

        {/* Semi-sensitive - Managers, HR, Self */}
        <Section title="Employment Details">
          <Field label="Joining Date" value={employee.joining_date?.split('T')[0]} />
          <Field label="Performance Rating" value={employee.performance_rating} masked={isMasked(employee.performance_rating)} />
        </Section>

        {/* Sensitive - HR/Admin/Self only */}
        <Section title="Personal Information" sensitive>
          <Field label="Personal Email" value={employee.personal_email} masked={isMasked(employee.personal_email)} />
          <Field label="Phone" value={employee.phone_number} masked={isMasked(employee.phone_number)} />
          <Field 
            label="Salary" 
            value={typeof employee.salary === 'number' ? `₹${employee.salary.toLocaleString()}` : employee.salary} 
            masked={isMasked(employee.salary)} 
          />
        </Section>
      </div>

      {canViewSensitive && (
        <div className="mt-6 p-3 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800">
          ⚠️ Sensitive data access logged for GDPR compliance
        </div>
      )}
    </div>
  );
};

const Section: React.FC<{ title: string; children: React.ReactNode; sensitive?: boolean }> = ({ title, children, sensitive }) => (
  <div className={`p-4 rounded-lg border ${sensitive ? 'border-red-200 bg-red-50' : 'border-gray-200 bg-white'}`}>
    <h2 className="font-semibold mb-3 flex items-center">
      {title}
      {sensitive && <span className="ml-2 text-xs text-red-600">(Sensitive)</span>}
    </h2>
    <div className="space-y-2">{children}</div>
  </div>
);

const Field: React.FC<{ label: string; value?: string | number | null; masked?: boolean }> = ({ label, value, masked }) => (
  <div className="flex justify-between">
    <span className="text-gray-600">{label}:</span>
    <span className={masked ? 'text-gray-400 italic' : 'font-medium'}>
      {masked ? '🔒 Restricted' : value || '-'}
    </span>
  </div>
);

export default EmployeeDetail;
