/** Line Manager Dashboard - Direct reports only */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi, api } from '../services/api';
import { PageHeader } from '../components/PageHeader';
import { ManagerCourseAssignments } from '../components/ManagerCourseAssignments';
import { Users, Target, Calendar, TrendingUp, RefreshCw, AlertCircle, BookOpen } from 'lucide-react';

interface TeamMember {
  id: number;
  employee_id: string;
  name: string;
  capability?: string;
  pathway?: string; // For skill filtering
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

interface AllEmployee {
  id: number;
  employee_id: string;
  name: string;
  company_email?: string;
  line_manager_id?: number;
}

interface EmployeeSkillForRating {
  id: number;
  skill_id: number;
  skill_name: string;
  skill_category?: string;
  current_rating?: string;
}

export const LMDashboard: React.FC = () => {
  const [directReports, setDirectReports] = useState<TeamMember[]>([]);
  const [teamSkills, setTeamSkills] = useState<TeamSkill[]>([]);
  const [allEmployees, setAllEmployees] = useState<AllEmployee[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [assigning, setAssigning] = useState<number | null>(null);
  const [debugInfo, setDebugInfo] = useState<DebugInfo | null>(null);
  const [activeTab, setActiveTab] = useState<'team' | 'skills' | 'courses' | 'performance' | 'assign'>('team');
  // Rate Skills Modal state
  const [showRateSkillsModal, setShowRateSkillsModal] = useState(false);
  const [ratingEmployee, setRatingEmployee] = useState<TeamMember | null>(null);
  const [employeeSkillsForRating, setEmployeeSkillsForRating] = useState<EmployeeSkillForRating[]>([]);
  const [loadingEmployeeSkills, setLoadingEmployeeSkills] = useState(false);
  const [skillRatings, setSkillRatings] = useState<Record<number, string>>({});
  const [savingRatings, setSavingRatings] = useState(false);
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

  const handleRateSkills = async (employee: TeamMember) => {
    setRatingEmployee(employee);
    setShowRateSkillsModal(true);
    setLoadingEmployeeSkills(true);
    setSkillRatings({});
    
    try {
      // Fetch skills with band requirements from the pathway
      const pathwayToUse = employee.pathway || employee.capability;
      const employeeBand = employee.band || 'A'; // Default to 'A' if no band
      
      console.log('[RateSkills] Employee:', employee.name, 'Pathway:', employee.pathway, 'Capability:', employee.capability, 'Using:', pathwayToUse, 'Band:', employeeBand);
      
      // Fetch pathway skills with band requirements (public endpoint for managers)
      const pathwaySkillsRes = await api.get(`/api/role-requirements/pathway/${pathwayToUse}/skills/public`);
      
      // Also fetch employee's current skill ratings (if they have any saved)
      let existingRatings: Record<number, string> = {};
      try {
        const empSkillsRes = await api.get(`/api/user-skills/employee/${employee.employee_id}`);
        if (empSkillsRes.data && empSkillsRes.data.length > 0) {
          empSkillsRes.data.forEach((es: any) => {
            if (es.rating) {
              existingRatings[es.skill_id] = es.rating;
            }
          });
        }
      } catch (e) {
        console.log('No existing skills for employee');
      }
      
      // pathwaySkillsRes.data is grouped by category: { "Category": [skills...] }
      if (pathwaySkillsRes.data && Object.keys(pathwaySkillsRes.data).length > 0) {
        const allSkills: EmployeeSkillForRating[] = [];
        const defaultRatings: Record<number, string> = {};
        
        // Flatten the grouped skills and get default rating from band requirements
        Object.entries(pathwaySkillsRes.data).forEach(([category, skills]: [string, any]) => {
          skills.forEach((skill: any) => {
            // Get the expected rating for this employee's band
            const bandRating = skill.band_requirements?.[employeeBand];
            // Use existing rating if available, otherwise use band requirement as default
            const rating = existingRatings[skill.skill_id] || bandRating;
            
            allSkills.push({
              id: 0,
              skill_id: skill.skill_id,
              skill_name: skill.skill_name,
              skill_category: skill.skill_category || category || 'General',
              current_rating: rating
            });
            
            if (rating) {
              defaultRatings[skill.skill_id] = rating;
            }
          });
        });
        
        setSkillRatings(defaultRatings);
        setEmployeeSkillsForRating(allSkills);
      } else {
        // No skills found for this pathway
        setEmployeeSkillsForRating([]);
      }
    } catch (error) {
      console.error('Failed to load employee skills:', error);
      setEmployeeSkillsForRating([]);
    } finally {
      setLoadingEmployeeSkills(false);
    }
  };

  const handleSaveRatings = async () => {
    if (!ratingEmployee) return;
    
    setSavingRatings(true);
    try {
      // Save each skill rating
      for (const [skillId, rating] of Object.entries(skillRatings)) {
        if (rating) {
          await api.post('/api/user-skills/', {
            employee_id: ratingEmployee.employee_id,
            skill_name: employeeSkillsForRating.find(s => s.skill_id === parseInt(skillId))?.skill_name,
            rating: rating
          });
        }
      }
      alert('Ratings saved successfully!');
      setShowRateSkillsModal(false);
      await loadData();
    } catch (error: any) {
      console.error('Failed to save ratings:', error);
      alert('Failed to save ratings: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSavingRatings(false);
    }
  };

  const loadAllEmployees = async () => {
    try {
      const res = await api.get('/api/admin/employees', { params: { limit: 100 } });
      setAllEmployees(res.data);
    } catch (error) {
      console.error('Failed to load employees:', error);
    }
  };

  const assignDirectReport = async (employeeId: number) => {
    try {
      setAssigning(employeeId);
      const res = await api.post(`/api/dashboard/lm/assign-direct-report?employee_id=${employeeId}`);
      if (res.data.success) {
        alert(`Successfully assigned ${res.data.employee.name} as your direct report`);
        await loadData();
        await loadAllEmployees();
      } else {
        alert('Failed: ' + res.data.error);
      }
    } catch (error: any) {
      console.error('Failed to assign:', error);
      alert('Failed to assign: ' + (error.response?.data?.detail || error.message));
    } finally {
      setAssigning(null);
    }
  };

  // Load all employees when switching to assign tab
  useEffect(() => {
    if (activeTab === 'assign' && allEmployees.length === 0) {
      loadAllEmployees();
    }
  }, [activeTab]);

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

        {/* Action Buttons */}
        <div className="mb-4 flex justify-end gap-3">
          <button
            onClick={() => navigate('/manager/template-assessment')}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <Target className="w-4 h-4" />
            Assess Employee Skills
          </button>
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
        <div className="flex space-x-4 mb-6 border-b overflow-x-auto">
          <TabButton active={activeTab === 'team'} onClick={() => setActiveTab('team')}>
            <Users className="w-4 h-4 mr-2" /> Direct Reports
          </TabButton>
          <TabButton active={activeTab === 'skills'} onClick={() => setActiveTab('skills')}>
            <Target className="w-4 h-4 mr-2" /> Team Skills
          </TabButton>
          <TabButton active={activeTab === 'courses'} onClick={() => setActiveTab('courses')}>
            <BookOpen className="w-4 h-4 mr-2" /> Course Assignments
          </TabButton>
          <TabButton active={activeTab === 'performance'} onClick={() => setActiveTab('performance')}>
            <TrendingUp className="w-4 h-4 mr-2" /> Performance
          </TabButton>
          <TabButton active={activeTab === 'assign'} onClick={() => setActiveTab('assign')}>
            <Users className="w-4 h-4 mr-2" /> Assign Employees
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
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Actions</th>
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
                      <td className="px-4 py-3 text-sm">
                        {member.id > 0 && (
                          <button
                            onClick={() => handleRateSkills(member)}
                            className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
                          >
                            Rate Skills
                          </button>
                        )}
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

        {/* Course Assignments Tab */}
        {activeTab === 'courses' && (
          <div className="bg-white rounded-lg shadow p-6">
            <ManagerCourseAssignments />
          </div>
        )}

        {/* Performance Tab */}
        {activeTab === 'performance' && (
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-500">Performance tracking coming soon...</p>
          </div>
        )}

        {/* Assign Employees Tab */}
        {activeTab === 'assign' && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b">
              <h3 className="font-semibold">Assign Employees as Direct Reports</h3>
              <p className="text-sm text-gray-500 mt-1">
                Select employees to add them as your direct reports. This will allow you to rate their skills.
              </p>
            </div>
            {allEmployees.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                Loading employees...
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Employee ID</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Name</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Email</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Current Manager ID</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {allEmployees.map((emp) => {
                    const isAlreadyReport = directReports.some(r => r.id === emp.id);
                    const isCurrentManager = debugInfo?.manager_employee?.id === emp.id;
                    return (
                      <tr key={emp.id} className={`hover:bg-gray-50 ${isAlreadyReport ? 'bg-green-50' : ''}`}>
                        <td className="px-4 py-3 text-sm">{emp.employee_id}</td>
                        <td className="px-4 py-3 text-sm font-medium">{emp.name}</td>
                        <td className="px-4 py-3 text-sm">{emp.company_email || '-'}</td>
                        <td className="px-4 py-3 text-sm">{emp.line_manager_id || '-'}</td>
                        <td className="px-4 py-3 text-sm">
                          {isCurrentManager ? (
                            <span className="text-gray-400">This is you</span>
                          ) : isAlreadyReport ? (
                            <span className="text-green-600">✓ Your report</span>
                          ) : (
                            <button
                              onClick={() => assignDirectReport(emp.id)}
                              disabled={assigning === emp.id}
                              className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:opacity-50"
                            >
                              {assigning === emp.id ? 'Assigning...' : 'Assign to Me'}
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>

      {/* Rate Skills Modal */}
      {showRateSkillsModal && ratingEmployee && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
            <div className="p-4 border-b flex justify-between items-center">
              <div>
                <h3 className="text-lg font-semibold">Rate Skills for {ratingEmployee.name}</h3>
                <p className="text-sm text-gray-500">Pathway: {ratingEmployee.pathway || ratingEmployee.capability || 'Not assigned'}</p>
              </div>
              <button
                onClick={() => setShowRateSkillsModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4">
              {loadingEmployeeSkills ? (
                <div className="text-center py-8 text-gray-500">Loading skills...</div>
              ) : employeeSkillsForRating.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p className="mb-2">No skills found for the "{ratingEmployee?.pathway || ratingEmployee?.capability || 'Unknown'}" pathway.</p>
                  <p className="text-sm">Please ensure skills are configured for this pathway in Career Pathways.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {/* Group by category */}
                  {Object.entries(
                    employeeSkillsForRating.reduce<Record<string, EmployeeSkillForRating[]>>((acc, skill) => {
                      const cat = skill.skill_category || 'General';
                      if (!acc[cat]) acc[cat] = [];
                      acc[cat].push(skill);
                      return acc;
                    }, {})
                  ).map(([category, skills]) => (
                    <div key={category} className="border rounded-lg overflow-hidden">
                      <div className="bg-gray-50 px-4 py-2 font-medium text-gray-700">
                        {category} ({skills.length} skills)
                      </div>
                      <div className="divide-y">
                        {skills.map((skill) => (
                          <div key={skill.skill_id} className="px-4 py-3 flex items-center justify-between">
                            <span className="text-sm">{skill.skill_name}</span>
                            <select
                              value={skillRatings[skill.skill_id] || ''}
                              onChange={(e) => setSkillRatings(prev => ({ ...prev, [skill.skill_id]: e.target.value }))}
                              className="px-3 py-1 border rounded text-sm"
                            >
                              <option value="">Select Rating</option>
                              <option value="Beginner">Beginner</option>
                              <option value="Developing">Developing</option>
                              <option value="Intermediate">Intermediate</option>
                              <option value="Advanced">Advanced</option>
                              <option value="Expert">Expert</option>
                            </select>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            <div className="p-4 border-t flex justify-end gap-2">
              <button
                onClick={() => setShowRateSkillsModal(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveRatings}
                disabled={savingRatings || Object.keys(skillRatings).length === 0}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {savingRatings ? 'Saving...' : 'Save Ratings'}
              </button>
            </div>
          </div>
        </div>
      )}
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
