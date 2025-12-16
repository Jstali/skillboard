/** Line Manager Dashboard - Direct reports only */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi, api } from '../services/api';
import { PageHeader } from '../components/PageHeader';
import { Users, Target, Calendar, TrendingUp, RefreshCw, AlertCircle } from 'lucide-react';

interface TeamMember {
  id: number;
  employee_id: string;
  name: string;
  capability?: string;
  band?: string;
  skills_count?: number;
  source?: string; // "local", "hrms", or "project"
  project_name?: string; // If from project assignment
}

interface TeamSkill {
  employee_id: string;
  name: string;
  skills: { name: string; rating: string | null }[];
}

interface DebugInfo {
  user: {
    id: number;
    email: string;
    employee_id: string | null;
    role_id: number;
  };
  manager_employee: {
    id: number;
    employee_id: string;
    name: string;
  } | null;
  local_direct_reports: any[];
  hrms_direct_reports: any[];
  issues: string[];
}

export const LMDashboard: React.FC = () => {
  const [directReports, setDirectReports] = useState<TeamMember[]>([]);
  const [teamSkills, setTeamSkills] = useState<TeamSkill[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [debugInfo, setDebugInfo] = useState<DebugInfo | null>(null);
  const [activeTab, setActiveTab] = useState<'team' | 'skills' | 'performance'>('team');
  const navigate = useNavigate();
  const user = authApi.getUser();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      console.log('[LMDashboard] Fetching direct reports...');
      const [reportsRes, skillsRes, debugRes] = await Promise.all([
        api.get('/api/dashboard/lm/direct-reports'),
        api.get('/api/dashboard/lm/team-skills'),
        api.get('/api/dashboard/lm/debug-manager-info').catch(() => ({ data: null }))
      ]);
      console.log('[LMDashboard] Direct reports response:', reportsRes.data);
      console.log('[LMDashboard] Total reports:', reportsRes.data.length);
      console.log('[LMDashboard] Debug info:', debugRes.data);
      setDirectReports(reportsRes.data);
      setTeamSkills(skillsRes.data);
      setDebugInfo(debugRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const syncHRMSReports = async () => {
    try {
      setSyncing(true);
      const res = await api.post('/api/dashboard/lm/sync-hrms-reports');
      console.log('[LMDashboard] Sync result:', res.data);
      alert(`Synced ${res.data.synced_employees?.length || 0} employees, created ${res.data.created_employees?.length || 0} new records`);
      await loadData(); // Reload data after sync
    } catch (error: any) {
      console.error('Failed to sync:', error);
      alert('Failed to sync: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSyncing(false);
    }
  };

  const handleLogout = () => {
    authApi.logout();
    navigate('/login');
  };

  if (loading) return <div className="p-6">Loading...</div>;

  return (
    <div className="min-h-screen bg-gray-50">
      <PageHeader
        title="Line Manager Dashboard"
        subtitle={`Welcome, ${user?.email}`}
        onLogout={handleLogout}
      />

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Debug Info Banner */}
        {debugInfo && debugInfo.issues && debugInfo.issues.length > 0 && (
          <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-yellow-800">Configuration Issues Detected</h4>
                <ul className="mt-1 text-sm text-yellow-700 list-disc list-inside">
                  {debugInfo.issues.map((issue, idx) => (
                    <li key={idx}>{issue}</li>
                  ))}
                </ul>
                <button
                  onClick={syncHRMSReports}
                  disabled={syncing}
                  className="mt-2 px-3 py-1 bg-yellow-600 text-white text-sm rounded hover:bg-yellow-700 disabled:opacity-50"
                >
                  {syncing ? 'Syncing...' : 'Sync from HRMS'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <StatCard icon={<Users />} label="Direct Reports" value={directReports.length} />
          <StatCard icon={<Target />} label="Skill Gaps" value={0} />
          <StatCard icon={<Calendar />} label="Pending Reviews" value={0} />
          <StatCard icon={<TrendingUp />} label="Avg Team Rating" value={0} />
        </div>

        {/* Sync Button */}
        <div className="mb-4 flex justify-end">
          <button
            onClick={syncHRMSReports}
            disabled={syncing}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
            {syncing ? 'Syncing...' : 'Sync from HRMS'}
          </button>
        </div>

        {/* Tabs */}
        <div className="flex space-x-4 mb-6 border-b">
          <TabButton active={activeTab === 'team'} onClick={() => setActiveTab('team')}>
            <Users className="w-4 h-4 mr-2" /> Direct Reports
          </TabButton>
          <TabButton active={activeTab === 'skills'} onClick={() => setActiveTab('skills')}>
            <Target className="w-4 h-4 mr-2" /> Team Skills
          </TabButton>
          <TabButton active={activeTab === 'performance'} onClick={() => setActiveTab('performance')}>
            <TrendingUp className="w-4 h-4 mr-2" /> Performance
          </TabButton>
        </div>

        {/* Team Tab */}
        {activeTab === 'team' && (
          <div className="bg-white rounded-lg shadow">
            {directReports.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No direct reports assigned to you.
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Employee ID</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Name</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Capability</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Band</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Skills</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Source</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {directReports.map((member) => (
                    <tr key={member.employee_id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm">{member.employee_id}</td>
                      <td className="px-4 py-3 text-sm font-medium">{member.name}</td>
                      <td className="px-4 py-3 text-sm">{member.capability || '-'}</td>
                      <td className="px-4 py-3 text-sm">{member.band || '-'}</td>
                      <td className="px-4 py-3 text-sm">{member.skills_count || 0}</td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          member.source === 'hrms' 
                            ? 'bg-blue-100 text-blue-800' 
                            : member.source === 'project'
                            ? 'bg-purple-100 text-purple-800'
                            : 'bg-green-100 text-green-800'
                        }`}>
                          {member.source === 'hrms' ? 'HRMS' : member.source === 'project' ? `Project: ${member.project_name || 'N/A'}` : 'Direct'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Skills Tab */}
        {activeTab === 'skills' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-semibold mb-4">Team Skills Overview</h3>
            {teamSkills.length === 0 ? (
              <p className="text-gray-500">No skill data available.</p>
            ) : (
              <div className="space-y-4">
                {teamSkills.map((member) => (
                  <div key={member.employee_id} className="border rounded-lg p-4">
                    <h4 className="font-medium mb-2">{member.name}</h4>
                    <div className="flex flex-wrap gap-2">
                      {member.skills.map((skill, idx) => (
                        <span key={idx} className={`px-2 py-1 rounded text-sm ${
                          skill.rating === 'Expert' ? 'bg-green-100 text-green-800' :
                          skill.rating === 'Advanced' ? 'bg-blue-100 text-blue-800' :
                          skill.rating === 'Intermediate' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {skill.name}: {skill.rating || 'Not Rated'}
                        </span>
                      ))}
                      {member.skills.length === 0 && <span className="text-gray-400">No skills recorded</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Performance Tab */}
        {activeTab === 'performance' && (
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-500">Performance tracking coming soon...</p>
          </div>
        )}
      </div>
    </div>
  );
};

const StatCard: React.FC<{ icon: React.ReactNode; label: string; value: number }> = ({ icon, label, value }) => (
  <div className="bg-white rounded-lg shadow p-4 flex items-center">
    <div className="p-3 rounded-lg bg-blue-100 text-blue-600 mr-4">{icon}</div>
    <div>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-sm text-gray-600">{label}</p>
    </div>
  </div>
);

const TabButton: React.FC<{ active: boolean; onClick: () => void; children: React.ReactNode }> = ({ active, onClick, children }) => (
  <button
    onClick={onClick}
    className={`flex items-center px-4 py-2 border-b-2 ${active ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-600'}`}
  >
    {children}
  </button>
);

export default LMDashboard;
