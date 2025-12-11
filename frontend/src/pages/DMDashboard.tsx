/** Delivery Manager Dashboard - Project team view */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi, api } from '../services/api';
import { PageHeader } from '../components/PageHeader';
import { Users, Briefcase, Target, Calendar } from 'lucide-react';

interface TeamMember {
  id: number;
  employee_id: string;
  name: string;
  capability?: string;
  band?: string;
}

export const DMDashboard: React.FC = () => {
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'team' | 'projects' | 'staffing'>('team');
  const navigate = useNavigate();
  const user = authApi.getUser();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const res = await api.get('/api/dashboard/dm/team-overview');
      setTeam(res.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
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
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <StatCard icon={<Users />} label="Team Members" value={team.length} />
          <StatCard icon={<Briefcase />} label="Active Projects" value={0} />
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
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {team.map((member) => (
                    <tr key={member.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm">{member.employee_id}</td>
                      <td className="px-4 py-3 text-sm font-medium">{member.name}</td>
                      <td className="px-4 py-3 text-sm">{member.capability || '-'}</td>
                      <td className="px-4 py-3 text-sm">{member.band || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Projects Tab */}
        {activeTab === 'projects' && (
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-500">Project management coming soon...</p>
            <button 
              onClick={() => navigate('/test/projects')}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg"
            >
              Go to Projects
            </button>
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
