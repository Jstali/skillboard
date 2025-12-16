/** HR Dashboard - Full employee access with sensitive data */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi, api, UploadResponse } from '../services/api';
import { PageHeader } from '../components/PageHeader';
import { TemplateManagement } from '../components/TemplateManagement';
import { Users, FileText, BarChart3, Settings, Search, UserPlus, Download, Upload } from 'lucide-react';

interface Employee {
  id: number;
  employee_id: string;
  name: string;
  first_name?: string;
  last_name?: string;
  company_email?: string;
  department?: string;
  capability?: string;
  band?: string;
  grade?: string;
}

interface HRStats {
  total_employees: number;
  by_capability: Record<string, number>;
  by_department: Record<string, number>;
  by_band: Record<string, number>;
}

export const HRDashboard: React.FC = () => {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [stats, setStats] = useState<HRStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState<'directory' | 'analytics' | 'templates'>('directory');
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [uploadError, setUploadError] = useState<string>('');
  const navigate = useNavigate();
  const user = authApi.getUser();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [empRes, statsRes] = await Promise.all([
        api.get('/api/dashboard/hr/employees?limit=100'),
        api.get('/api/dashboard/hr/stats')
      ]);
      setEmployees(empRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Failed to load HR data:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredEmployees = employees.filter(e =>
    e.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    e.employee_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    e.department?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleLogout = () => {
    authApi.logout();
    navigate('/login');
  };

  if (loading) return <div className="p-6">Loading...</div>;

  return (
    <div className="min-h-screen bg-gray-50">
      <PageHeader
        title="HR Dashboard"
        subtitle={`Welcome, ${user?.email}`}
        onLogout={handleLogout}
      />

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <StatCard icon={<Users />} label="Total Employees" value={stats?.total_employees || 0} color="blue" />
          <StatCard icon={<BarChart3 />} label="Capabilities" value={Object.keys(stats?.by_capability || {}).length} color="green" />
          <StatCard icon={<FileText />} label="Departments" value={Object.keys(stats?.by_department || {}).length} color="purple" />
          <StatCard icon={<Settings />} label="Bands" value={Object.keys(stats?.by_band || {}).length} color="orange" />
        </div>

        {/* Upload Result Messages */}
        {uploadError && (
          <div className="mb-4 rounded-md bg-red-50 p-4">
            <div className="text-sm text-red-800">{uploadError}</div>
            <button onClick={() => setUploadError('')} className="text-xs text-red-600 underline mt-1">Dismiss</button>
          </div>
        )}
        {uploadResult && (
          <div className="mb-4 rounded-md bg-green-50 p-4">
            <p className="text-sm font-semibold text-green-800">{uploadResult.message}</p>
            <p className="text-xs text-green-600 mt-1">
              Processed: {uploadResult.rows_processed} | Created: {uploadResult.rows_created} | Updated: {uploadResult.rows_updated}
            </p>
            <button onClick={() => setUploadResult(null)} className="text-xs text-green-600 underline mt-1">Dismiss</button>
          </div>
        )}

        {/* Tabs */}
        <div className="flex space-x-4 mb-6 border-b">
          <TabButton active={activeTab === 'directory'} onClick={() => setActiveTab('directory')}>
            <Users className="w-4 h-4 mr-2" /> Employee Directory
          </TabButton>
          <TabButton active={activeTab === 'analytics'} onClick={() => setActiveTab('analytics')}>
            <BarChart3 className="w-4 h-4 mr-2" /> Analytics
          </TabButton>
          <TabButton active={activeTab === 'templates'} onClick={() => setActiveTab('templates')}>
            <Upload className="w-4 h-4 mr-2" /> Skill Templates
          </TabButton>
        </div>

        {/* Directory Tab */}
        {activeTab === 'directory' && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search employees..."
                  className="pl-10 pr-4 py-2 border rounded-lg w-full"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              <div className="flex space-x-2">
                <button 
                  onClick={() => navigate('/admin/users')}
                  className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  <UserPlus className="w-4 h-4 mr-2" /> Manage Users
                </button>
                <button className="flex items-center px-4 py-2 border rounded-lg hover:bg-gray-50">
                  <Download className="w-4 h-4 mr-2" /> Export
                </button>
              </div>
            </div>

            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Employee ID</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Name</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Email</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Department</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Capability</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Band</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {filteredEmployees.map((emp) => (
                  <tr key={emp.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm">{emp.employee_id}</td>
                    <td className="px-4 py-3 text-sm font-medium">{emp.name}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{emp.company_email}</td>
                    <td className="px-4 py-3 text-sm">{emp.department || '-'}</td>
                    <td className="px-4 py-3 text-sm">{emp.capability || '-'}</td>
                    <td className="px-4 py-3 text-sm">{emp.band || '-'}</td>
                    <td className="px-4 py-3 text-sm">
                      <button className="text-blue-600 hover:underline">View</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filteredEmployees.length === 0 && (
              <div className="text-center py-8 text-gray-500">No employees found</div>
            )}
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="font-semibold mb-4">By Capability</h3>
              {Object.entries(stats?.by_capability || {}).map(([cap, count]) => (
                <div key={cap} className="flex justify-between py-2 border-b">
                  <span>{cap}</span>
                  <span className="font-medium">{count}</span>
                </div>
              ))}
              {Object.keys(stats?.by_capability || {}).length === 0 && (
                <p className="text-gray-500">No data available</p>
              )}
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="font-semibold mb-4">By Department</h3>
              {Object.entries(stats?.by_department || {}).map(([dept, count]) => (
                <div key={dept} className="flex justify-between py-2 border-b">
                  <span>{dept}</span>
                  <span className="font-medium">{count}</span>
                </div>
              ))}
              {Object.keys(stats?.by_department || {}).length === 0 && (
                <p className="text-gray-500">No data available</p>
              )}
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="font-semibold mb-4">By Band</h3>
              {Object.entries(stats?.by_band || {}).map(([band, count]) => (
                <div key={band} className="flex justify-between py-2 border-b">
                  <span>{band || 'Unassigned'}</span>
                  <span className="font-medium">{count}</span>
                </div>
              ))}
              {Object.keys(stats?.by_band || {}).length === 0 && (
                <p className="text-gray-500">No data available</p>
              )}
            </div>
          </div>
        )}

        {/* Templates Tab - Using TemplateManagement component */}
        {activeTab === 'templates' && (
          <div>
            <div className="mb-4 flex gap-2">
              <button 
                onClick={() => navigate('/admin/template-assignment')}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Assign Templates to Employees
              </button>
              <button 
                onClick={() => navigate('/admin/skill-gaps')}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                View Skill Gap Analysis
              </button>
            </div>
            
            <TemplateManagement
              onUploadSuccess={(result) => {
                setUploadResult({
                  message: result.message || 'Template uploaded successfully',
                  rows_processed: result.templates_created || result.rows_processed || 0,
                  rows_created: result.templates_created || result.rows_created || 0,
                  rows_updated: result.rows_updated || 0,
                });
              }}
              onUploadError={(error) => setUploadError(error)}
            />
          </div>
        )}
      </div>
    </div>
  );
};

const StatCard: React.FC<{ icon: React.ReactNode; label: string; value: number; color: string }> = ({ icon, label, value, color }) => {
  const colors: Record<string, string> = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    purple: 'bg-purple-100 text-purple-600',
    orange: 'bg-orange-100 text-orange-600'
  };
  return (
    <div className="bg-white rounded-lg shadow p-4 flex items-center">
      <div className={`p-3 rounded-lg ${colors[color]} mr-4`}>{icon}</div>
      <div>
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-sm text-gray-600">{label}</p>
      </div>
    </div>
  );
};

const TabButton: React.FC<{ active: boolean; onClick: () => void; children: React.ReactNode }> = ({ active, onClick, children }) => (
  <button
    onClick={onClick}
    className={`flex items-center px-4 py-2 border-b-2 ${active ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-600 hover:text-gray-900'}`}
  >
    {children}
  </button>
);

export default HRDashboard;
