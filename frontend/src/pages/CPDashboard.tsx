/** Capability Partner Dashboard - Capability members only */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi, api } from '../services/api';
import { PageHeader } from '../components/PageHeader';
import { Users, Grid3X3, Award, BookOpen } from 'lucide-react';

interface CapabilityMember {
  id: number;
  employee_id: string;
  name: string;
  capability?: string;
  band?: string;
  company_email?: string;
}

export const CPDashboard: React.FC = () => {
  const [members, setMembers] = useState<CapabilityMember[]>([]);
  const [skillMatrix, setSkillMatrix] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'members' | 'matrix' | 'certifications'>('members');
  const navigate = useNavigate();
  const user = authApi.getUser();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [membersRes, matrixRes] = await Promise.all([
        api.get('/api/dashboard/cp/members'),
        api.get('/api/dashboard/cp/skill-matrix')
      ]);
      setMembers(membersRes.data);
      setSkillMatrix(matrixRes.data);
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

  const capability = members[0]?.capability || 'Your Capability';

  return (
    <div className="min-h-screen bg-gray-50">
      <PageHeader
        title="Capability Partner Dashboard"
        subtitle={`${capability} - ${user?.email}`}
        onLogout={handleLogout}
      />

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <StatCard icon={<Users />} label="Capability Members" value={members.length} color="blue" />
          <StatCard icon={<Grid3X3 />} label="Skills Tracked" value={skillMatrix.reduce((acc, m) => acc + m.skills.length, 0)} color="green" />
          <StatCard icon={<Award />} label="Certifications" value={0} color="purple" />
          <StatCard icon={<BookOpen />} label="Learning Paths" value={0} color="orange" />
        </div>

        {/* Tabs */}
        <div className="flex space-x-4 mb-6 border-b">
          <TabButton active={activeTab === 'members'} onClick={() => setActiveTab('members')}>
            <Users className="w-4 h-4 mr-2" /> Capability Members
          </TabButton>
          <TabButton active={activeTab === 'matrix'} onClick={() => setActiveTab('matrix')}>
            <Grid3X3 className="w-4 h-4 mr-2" /> Skill Matrix
          </TabButton>
          <TabButton active={activeTab === 'certifications'} onClick={() => setActiveTab('certifications')}>
            <Award className="w-4 h-4 mr-2" /> Certifications
          </TabButton>
        </div>

        {/* Members Tab */}
        {activeTab === 'members' && (
          <div className="bg-white rounded-lg shadow">
            {members.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No members in your capability.
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Employee ID</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Name</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Email</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Band</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {members.map((member) => (
                    <tr key={member.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm">{member.employee_id}</td>
                      <td className="px-4 py-3 text-sm font-medium">{member.name}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{member.company_email}</td>
                      <td className="px-4 py-3 text-sm">{member.band || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Skill Matrix Tab */}
        {activeTab === 'matrix' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-semibold mb-4">Skill Matrix - {capability}</h3>
            {skillMatrix.length === 0 ? (
              <p className="text-gray-500">No skill data available.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium">Employee</th>
                      <th className="px-3 py-2 text-left font-medium">Skills</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {skillMatrix.map((member) => (
                      <tr key={member.employee_id}>
                        <td className="px-3 py-2 font-medium">{member.name}</td>
                        <td className="px-3 py-2">
                          <div className="flex flex-wrap gap-1">
                            {member.skills.map((s: any, idx: number) => (
                              <span key={idx} className={`px-2 py-0.5 rounded text-xs ${
                                s.rating === 'Expert' ? 'bg-green-100 text-green-800' :
                                s.rating === 'Advanced' ? 'bg-blue-100 text-blue-800' :
                                s.rating === 'Intermediate' ? 'bg-yellow-100 text-yellow-800' :
                                'bg-gray-100 text-gray-600'
                              }`}>
                                {s.rating || 'N/A'}
                              </span>
                            ))}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Certifications Tab */}
        {activeTab === 'certifications' && (
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-500">Certification tracking coming soon...</p>
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
    className={`flex items-center px-4 py-2 border-b-2 ${active ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-600'}`}
  >
    {children}
  </button>
);

export default CPDashboard;
