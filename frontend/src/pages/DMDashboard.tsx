/** Delivery Manager Dashboard - Location-based team view */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi, api } from '../services/api';
import { PageHeader } from '../components/PageHeader';
import { Users, Briefcase, Target, Calendar, RefreshCw, MapPin, AlertCircle } from 'lucide-react';

interface TeamMember {
  id: number;
  employee_id: string;
  name: string;
  capability?: string;
  band?: string;
  location?: string;
  projects_count?: number;
}

interface HRMSProject {
  id?: number;
  project_id?: string;
  name: string;
  client_name?: string;
  status?: string;
  manager_name?: string;
}

interface DebugInfo {
  dm_employee?: {
    location_id?: string;
    name?: string;
  };
  location?: string;
  employees_in_location?: number;
  issues?: string[];
}

export const DMDashboard: React.FC = () => {
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [projects, setProjects] = useState<HRMSProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingProjects, setLoadingProjects] = useState(false);
  const [projectsError, setProjectsError] = useState<string | null>(null);
  const [debugInfo, setDebugInfo] = useState<DebugInfo | null>(null);
  const [activeTab, setActiveTab] = useState<'team' | 'projects' | 'staffing'>('team');
  const navigate = useNavigate();
  const user = authApi.getUser();

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (activeTab === 'projects') {
      loadProjects();
    }
  }, [activeTab]);

  const loadData = async () => {
    try {
      const [teamRes, debugRes] = await Promise.all([
        api.get('/api/dashboard/dm/team-overview'),
        api.get('/api/dashboard/dm/debug-dm-info').catch(() => ({ data: null }))
      ]);
      setTeam(teamRes.data);
      setDebugInfo(debugRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadProjects = async () => {
    setLoadingProjects(true);
    setProjectsError(null);
    try {
      const res = await api.get('/api/dashboard/dm/projects');
      setProjects(res.data);
    } catch (error: any) {
      console.error('Failed to load projects from HRMS:', error);
      setProjectsError(error.response?.data?.detail || 'Failed to fetch projects from HRMS');
      setProjects([]);
    } finally {
      setLoadingProjects(false);
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
        title="Delivery Manager Dashboard"
        subtitle={`Welcome, ${user?.email}`}
        onLogout={handleLogout}
      />

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Location Info Banner */}
        {debugInfo && (
          <div className={`mb-4 p-4 rounded-lg ${debugInfo.location ? 'bg-blue-50 border border-blue-200' : 'bg-yellow-50 border border-yellow-200'}`}>
            <div className="flex items-start gap-2">
              {debugInfo.location ? (
                <>
                  <MapPin className="w-5 h-5 text-blue-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-blue-800">Location: {debugInfo.location}</h4>
                    <p className="text-sm text-blue-700">Showing {debugInfo.employees_in_location || team.length} employees in your location</p>
                  </div>
                </>
              ) : (
                <>
                  <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-yellow-800">No Location Set</h4>
                    <p className="text-sm text-yellow-700">Your employee record doesn't have a location. Showing all employees.</p>
                    {debugInfo.issues?.map((issue, idx) => (
                      <p key={idx} className="text-sm text-yellow-600">{issue}</p>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <StatCard icon={<Users />} label="Team Members" value={team.length} />
          <StatCard icon={<Briefcase />} label="Active Projects" value={projects.filter(p => p.status === 'Active').length} />
          <StatCard icon={<Target />} label="Skill Gaps" value={0} />
          <StatCard icon={<Calendar />} label="Upcoming Needs" value={0} />
        </div>

        {/* Tabs */}
        <div className="flex space-x-4 mb-6 border-b">
          <TabButton active={activeTab === 'team'} onClick={() => setActiveTab('team')}>
            <Users className="w-4 h-4 mr-2" /> Team Overview
          </TabButton>
          <TabButton active={activeTab === 'projects'} onClick={() => setActiveTab('projects')}>
            <Briefcase className="w-4 h-4 mr-2" /> Projects
          </TabButton>
          <TabButton active={activeTab === 'staffing'} onClick={() => setActiveTab('staffing')}>
            <Calendar className="w-4 h-4 mr-2" /> Staffing
          </TabButton>
        </div>

        {/* Team Tab */}
        {activeTab === 'team' && (
          <div className="bg-white rounded-lg shadow">
            {team.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No team members assigned.
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Employee ID</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Name</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Capability</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Band</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Location</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Projects</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {team.map((member) => (
                    <tr key={member.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm">{member.employee_id}</td>
                      <td className="px-4 py-3 text-sm font-medium">{member.name}</td>
                      <td className="px-4 py-3 text-sm">{member.capability || '-'}</td>
                      <td className="px-4 py-3 text-sm">{member.band || '-'}</td>
                      <td className="px-4 py-3 text-sm">{member.location || '-'}</td>
                      <td className="px-4 py-3 text-sm">{member.projects_count || 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Projects Tab */}
        {activeTab === 'projects' && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b flex justify-between items-center">
              <h3 className="font-semibold text-gray-800">Projects from HRMS</h3>
              <button
                onClick={loadProjects}
                disabled={loadingProjects}
                className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${loadingProjects ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
            
            {loadingProjects ? (
              <div className="p-8 text-center text-gray-500">Loading projects from HRMS...</div>
            ) : projectsError ? (
              <div className="p-8 text-center">
                <p className="text-red-500 mb-4">{projectsError}</p>
                <button
                  onClick={loadProjects}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg"
                >
                  Retry
                </button>
              </div>
            ) : projects.length === 0 ? (
              <div className="p-8 text-center text-gray-500">No projects found in HRMS.</div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Project ID</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Name</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Client</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Manager</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {projects.map((project, idx) => (
                    <tr key={project.project_id || idx} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm">{project.project_id || '-'}</td>
                      <td className="px-4 py-3 text-sm font-medium">{project.name}</td>
                      <td className="px-4 py-3 text-sm">{project.client_name || '-'}</td>
                      <td className="px-4 py-3 text-sm">{project.manager_name || '-'}</td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`px-2 py-1 rounded text-xs ${
                          project.status === 'Active' ? 'bg-green-100 text-green-800' :
                          project.status === 'Completed' ? 'bg-gray-100 text-gray-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {project.status || 'Unknown'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Staffing Tab */}
        {activeTab === 'staffing' && (
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-500">Staffing management coming soon...</p>
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

export default DMDashboard;
