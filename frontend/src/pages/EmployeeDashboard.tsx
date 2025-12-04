/** Employee Dashboard - Unified landing page with profile, skills, and learning. */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi, bandsApi, learningApi, userSkillsApi, BandAnalysis, CourseAssignment, EmployeeSkill } from '../services/api';
import NxzenLogo from '../images/Nxzen.jpg';

export const EmployeeDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'profile' | 'career' | 'learning'>('profile');
  const [analysis, setAnalysis] = useState<BandAnalysis | null>(null);
  const [assignments, setAssignments] = useState<CourseAssignment[]>([]);
  const [skills, setSkills] = useState<EmployeeSkill[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'below' | 'at' | 'above'>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [planToClose, setPlanToClose] = useState<Record<number, string>>({});
  // Custom skill form state
  const [customSkillName, setCustomSkillName] = useState('');
  const [customSkillCategory, setCustomSkillCategory] = useState('');
  const [customSkillRating, setCustomSkillRating] = useState<string>('Beginner');
  const [customSkillCertificate, setCustomSkillCertificate] = useState('');
  const [addingCustomSkill, setAddingCustomSkill] = useState(false);
  // Interested skill form state
  const [interestedSkillName, setInterestedSkillName] = useState('');
  const [interestedSkillCategory, setInterestedSkillCategory] = useState('');
  const [addingInterestedSkill, setAddingInterestedSkill] = useState(false);
  const navigate = useNavigate();
  const user = authApi.getUser();

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      if (activeTab === 'profile' || activeTab === 'career') {
        const [analysisData, skillsData] = await Promise.all([
          bandsApi.getMyAnalysis(),
          userSkillsApi.getMySkills()
        ]);
        setAnalysis(analysisData);
        setSkills(skillsData);
        
        // Load existing plans from notes
        const plans: Record<number, string> = {};
        analysisData.skill_gaps.forEach((gap) => {
          if (gap.notes) {
            plans[gap.skill_id] = gap.notes;
          }
        });
        setPlanToClose(plans);
      }
      
      if (activeTab === 'learning') {
        const assignmentsData = await learningApi.getMyAssignments();
        setAssignments(assignmentsData);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePlanChange = (skillId: number, value: string) => {
    setPlanToClose(prev => ({
      ...prev,
      [skillId]: value
    }));
  };

  const handlePlanBlur = async (skillId: number, employeeSkillId: number) => {
    const plan = planToClose[skillId];
    if (plan === undefined) return;
    
    try {
      await userSkillsApi.updateMySkill(employeeSkillId, {
        notes: plan
      });
    } catch (err) {
      console.error('Failed to save plan:', err);
    }
  };

  const handleAddCustomSkill = async () => {
    if (!customSkillName.trim()) return;
    setAddingCustomSkill(true);
    try {
      await userSkillsApi.createMySkill({
        skill_name: customSkillName.trim(),
        rating: customSkillRating as any,
        is_interested: false,
        is_custom: true,
        notes: customSkillCertificate ? `Certificate: ${customSkillCertificate}` : undefined,
      });
      setCustomSkillName('');
      setCustomSkillCategory('');
      setCustomSkillRating('Beginner');
      setCustomSkillCertificate('');
      loadData();
    } catch (err) {
      console.error('Failed to add custom skill:', err);
      alert('Failed to add custom skill. Please try again.');
    } finally {
      setAddingCustomSkill(false);
    }
  };

  const handleAddInterestedSkill = async () => {
    if (!interestedSkillName.trim()) return;
    setAddingInterestedSkill(true);
    try {
      await userSkillsApi.createMySkill({
        skill_name: interestedSkillName.trim(),
        is_interested: true,
        is_custom: true,
      });
      setInterestedSkillName('');
      setInterestedSkillCategory('');
      loadData();
    } catch (err) {
      console.error('Failed to add interested skill:', err);
      alert('Failed to add interested skill. Please try again.');
    } finally {
      setAddingInterestedSkill(false);
    }
  };

  // Calculate chart data
  const getSkillsByCategory = () => {
    const categoryMap: Record<string, number> = {};
    skills.filter(s => !s.is_interested).forEach(skill => {
      const category = skill.skill?.category || 'Uncategorized';
      categoryMap[category] = (categoryMap[category] || 0) + 1;
    });
    return Object.entries(categoryMap).map(([name, value]) => ({ name, value }));
  };

  const getSkillsByRating = () => {
    const ratingMap: Record<string, number> = {
      'Expert': 0, 'Advanced': 0, 'Intermediate': 0, 'Developing': 0, 'Beginner': 0
    };
    skills.filter(s => !s.is_interested && s.rating).forEach(skill => {
      if (skill.rating) ratingMap[skill.rating] = (ratingMap[skill.rating] || 0) + 1;
    });
    return Object.entries(ratingMap).map(([name, value]) => ({ name, value }));
  };

  const CHART_COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4'];
  const RATING_COLORS: Record<string, string> = {
    'Expert': '#9333EA', 'Advanced': '#F97316', 'Intermediate': '#EAB308', 'Developing': '#3B82F6', 'Beginner': '#22C55E'
  };

  // Filter and paginate skill gaps
  const filteredGaps = analysis?.skill_gaps.filter((gap) => {
    if (filter === 'below') return gap.gap < 0;
    if (filter === 'at') return gap.gap === 0;
    if (filter === 'above') return gap.gap > 0;
    return true;
  }) || [];

  // Sort: Skills with gaps (negative) first, then others
  const sortedGaps = [...filteredGaps].sort((a, b) => {
    // First, sort by gap status (negative gaps first)
    if (a.gap < 0 && b.gap >= 0) return -1;
    if (a.gap >= 0 && b.gap < 0) return 1;
    // Within same status, sort by gap value (most negative first, then ascending)
    return a.gap - b.gap;
  });

  const totalPages = Math.ceil(sortedGaps.length / rowsPerPage);
  const paginatedGaps = sortedGaps.slice(
    (currentPage - 1) * rowsPerPage,
    currentPage * rowsPerPage
  );

  // Reset to page 1 when filter changes
  useEffect(() => {
    setCurrentPage(1);
  }, [filter]);

  const getSkillLevelColor = (rating?: string) => {
    switch (rating) {
      case 'Expert':
        return 'bg-purple-100 text-purple-800';
      case 'Advanced':
        return 'bg-orange-100 text-orange-800';
      case 'Intermediate':
        return 'bg-yellow-100 text-yellow-800';
      case 'Developing':
        return 'bg-blue-100 text-blue-800';
      case 'Beginner':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Completed':
        return 'bg-green-100 text-green-800';
      case 'In Progress':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const pendingCourses = assignments.filter(a => a.status !== 'Completed').length;

  return (
    <div className="min-h-screen bg-[#F6F2F4]">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="w-full px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <img src={NxzenLogo} alt="Nxzen" className="h-8 w-8 object-cover rounded" />
            <span className="text-xl font-semibold text-gray-800">Nxzen</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm">
              <div className="font-medium text-gray-800">
                {((user as any)?.first_name && (user as any)?.last_name)
                  ? `${(user as any).first_name} ${(user as any).last_name}`
                  : (user?.email ? user.email.split('@')[0] : 'User')}
              </div>
              <div className="text-xs text-gray-500">{user?.email}</div>
            </div>
            <button
              onClick={() => { authApi.logout(); navigate('/login'); }}
              className="p-2 rounded-lg hover:bg-gray-100"
              title="Logout"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-red-600">
                <path d="M16 13v-2H7V8l-5 4 5 4v-3h9zm3-11H9c-1.1 0-2 .9-2 2v3h2V4h10v16H9v-2H7v3c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-5">
        {/* Quick Actions / Tabs */}
        <div className="mb-6">
          <h2 className="text-center text-lg font-semibold text-gray-800 mb-3">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <button
              onClick={() => setActiveTab('profile')}
              className={`flex items-center gap-3 p-3 rounded-lg shadow-sm hover:shadow-md transition-all ${
                activeTab === 'profile' 
                  ? 'bg-white ring-1 ring-blue-500' 
                  : 'bg-white'
              }`}
            >
              <div className={`flex-shrink-0 w-10 h-10 rounded-md flex items-center justify-center ${
                activeTab === 'profile' ? 'bg-gray-100' : 'bg-gray-50'
              }`}>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-gray-700">
                  <path fillRule="evenodd" d="M7.5 6a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM3.751 20.105a8.25 8.25 0 0116.498 0 .75.75 0 01-.437.695A18.683 18.683 0 0112 22.5c-2.786 0-5.433-.608-7.812-1.7a.75.75 0 01-.437-.695z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="text-left">
                <div className="text-sm font-semibold text-gray-900">My Profile</div>
                <div className="text-xs text-gray-500">View your details</div>
              </div>
            </button>

            <button
              onClick={() => setActiveTab('career')}
              className={`flex items-center gap-3 p-3 rounded-lg shadow-sm hover:shadow-md transition-all ${
                activeTab === 'career' 
                  ? 'bg-white ring-1 ring-green-500' 
                  : 'bg-white'
              }`}
            >
              <div className={`flex-shrink-0 w-10 h-10 rounded-md flex items-center justify-center ${
                activeTab === 'career' ? 'bg-green-50' : 'bg-gray-50'
              }`}>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-green-700">
                  <path fillRule="evenodd" d="M2.25 13.5a8.25 8.25 0 018.25-8.25.75.75 0 01.75.75v6.75H18a.75.75 0 01.75.75 8.25 8.25 0 01-16.5 0z" clipRule="evenodd" />
                  <path fillRule="evenodd" d="M12.75 3a.75.75 0 01.75-.75 8.25 8.25 0 018.25 8.25.75.75 0 01-.75.75h-7.5a.75.75 0 01-.75-.75V3z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="text-left">
                <div className="text-sm font-semibold text-gray-900">Career Engagement</div>
                <div className="text-xs text-gray-500">Track your progress</div>
              </div>
            </button>

            <button
              onClick={() => setActiveTab('learning')}
              className={`flex items-center gap-3 p-3 rounded-lg shadow-sm hover:shadow-md transition-all relative ${
                activeTab === 'learning' 
                  ? 'bg-white ring-1 ring-blue-500' 
                  : 'bg-white'
              }`}
            >
              <div className={`flex-shrink-0 w-10 h-10 rounded-md flex items-center justify-center ${
                activeTab === 'learning' ? 'bg-blue-50' : 'bg-gray-50'
              }`}>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-blue-700">
                  <path d="M11.7 2.805a.75.75 0 01.6 0A60.65 60.65 0 0122.83 8.72a.75.75 0 01-.231 1.337 49.949 49.949 0 00-9.902 3.912l-.003.002-.34.18a.75.75 0 01-.707 0A50.009 50.009 0 007.5 12.174v-.224c0-.131.067-.248.172-.311a54.614 54.614 0 014.653-2.52.75.75 0 00-.65-1.352 56.129 56.129 0 00-4.78 2.589 1.858 1.858 0 00-.859 1.228 49.803 49.803 0 00-4.634-1.527.75.75 0 01-.231-1.337A60.653 60.653 0 0111.7 2.805z" />
                  <path d="M13.06 15.473a48.45 48.45 0 017.666-3.282c.134 1.414.22 2.843.255 4.285a.75.75 0 01-.46.71 47.878 47.878 0 00-8.105 4.342.75.75 0 01-.832 0 47.877 47.877 0 00-8.104-4.342.75.75 0 01-.461-.71c.035-1.442.121-2.87.255-4.286A48.4 48.4 0 016 13.18v1.27a1.5 1.5 0 00-.14 2.508c-.09.38-.222.753-.397 1.11.452.213.901.434 1.346.661a6.729 6.729 0 00.551-1.608 1.5 1.5 0 00.14-2.67v-.645a48.549 48.549 0 013.44 1.668 2.25 2.25 0 002.12 0z" />
                  <path d="M4.462 19.462c.42-.419.753-.89 1-1.394.453.213.902.434 1.347.661a6.743 6.743 0 01-1.286 1.794.75.75 0 11-1.06-1.06z" />
                </svg>
              </div>
              <div className="text-left">
                <div className="text-sm font-semibold text-gray-900">Mandatory Learning</div>
                <div className="text-xs text-gray-500">Complete courses</div>
              </div>
              {pendingCourses > 0 && (
                <span className="absolute top-2 right-2 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                  {pendingCourses}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Profile Tab */}
        {activeTab === 'profile' && (
          <div className="space-y-6">
            {/* Profile Card */}
            <div className="bg-white rounded-md shadow-sm p-3">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-7 h-7 text-gray-600">
                    <path fillRule="evenodd" d="M7.5 6a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM3.751 20.105a8.25 8.25 0 0116.498 0 .75.75 0 01-.437.695A18.683 18.683 0 0112 22.5c-2.786 0-5.433-.608-7.812-1.7a.75.75 0 01-.437-.695z" clipRule="evenodd" />
                  </svg>
                </div>
                <h2 className="text-lg font-bold text-gray-900">
                  {((user as any)?.first_name && (user as any)?.last_name)
                    ? `${(user as any).first_name} ${(user as any).last_name}`
                    : analysis?.employee_name || 'Employee'}
                </h2>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
                <div>
                  <div className="text-xs text-gray-500 uppercase">Career Level</div>
                  <div className="text-sm font-semibold text-gray-900">{analysis?.band || 'L1'}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase">Employee ID</div>
                  <div className="text-sm font-semibold text-gray-900">{analysis?.employee_id || user?.employee_id || '-'}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase">Location</div>
                  <div className="text-sm font-semibold text-gray-900">Remote</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase">Line Manager</div>
                  <div className="text-sm font-semibold text-gray-900">-</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase">Expertise</div>
                  <div className="text-sm font-semibold text-gray-900">Digital & Programming</div>
                </div>
              </div>
            </div>

            {/* Skills Overview Charts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Skills vs Requirements - Pie Chart */}
              <div className="bg-white rounded-md shadow-sm p-4">
                <h3 className="text-lg font-bold text-gray-900 mb-4">Skills vs Requirements</h3>
                {loading ? (
                  <div className="h-48 flex items-center justify-center text-gray-500">Loading...</div>
                ) : !analysis ? (
                  <div className="h-48 flex items-center justify-center text-gray-500">No skills data</div>
                ) : (
                  <div className="flex items-center gap-4">
                    {/* Pie Chart for Below/At/Above Requirements */}
                    <div className="relative w-40 h-40 flex-shrink-0">
                      <svg viewBox="0 0 100 100" className="w-full h-full transform -rotate-90">
                        {(() => {
                          const data = [
                            { name: 'Below Requirement', value: analysis.skills_below_requirement, color: '#EAB308' },
                            { name: 'At Requirement', value: analysis.skills_at_requirement, color: '#6B7280' },
                            { name: 'Above Requirement', value: analysis.skills_above_requirement, color: '#22C55E' },
                          ].filter(d => d.value > 0);
                          const total = data.reduce((sum, d) => sum + d.value, 0);
                          if (total === 0) return null;
                          let cumulative = 0;
                          return data.map((item) => {
                            const percentage = (item.value / total) * 100;
                            const dashArray = `${percentage} ${100 - percentage}`;
                            const dashOffset = -cumulative;
                            cumulative += percentage;
                            return (
                              <circle
                                key={item.name}
                                cx="50" cy="50" r="40"
                                fill="transparent"
                                stroke={item.color}
                                strokeWidth="20"
                                strokeDasharray={dashArray}
                                strokeDashoffset={dashOffset}
                              />
                            );
                          });
                        })()}
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-gray-900">{analysis.total_skills}</div>
                          <div className="text-xs text-gray-500">Skills</div>
                        </div>
                      </div>
                    </div>
                    {/* Legend */}
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2 text-sm">
                        <div className="w-3 h-3 rounded-full flex-shrink-0 bg-yellow-500" />
                        <span className="text-gray-700">Below Requirement</span>
                        <span className="text-gray-500 ml-auto font-semibold">({analysis.skills_below_requirement})</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <div className="w-3 h-3 rounded-full flex-shrink-0 bg-gray-500" />
                        <span className="text-gray-700">At Requirement</span>
                        <span className="text-gray-500 ml-auto font-semibold">({analysis.skills_at_requirement})</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <div className="w-3 h-3 rounded-full flex-shrink-0 bg-green-500" />
                        <span className="text-gray-700">Above Requirement</span>
                        <span className="text-gray-500 ml-auto font-semibold">({analysis.skills_above_requirement})</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Skills by Rating - Bar Chart */}
              <div className="bg-white rounded-md shadow-sm p-4">
                <h3 className="text-lg font-bold text-gray-900 mb-4">Skills by Proficiency</h3>
                {loading ? (
                  <div className="h-48 flex items-center justify-center text-gray-500">Loading...</div>
                ) : (
                  <div className="space-y-3">
                    {getSkillsByRating().map((item) => {
                      const maxValue = Math.max(...getSkillsByRating().map(r => r.value), 1);
                      const percentage = (item.value / maxValue) * 100;
                      return (
                        <div key={item.name} className="flex items-center gap-3">
                          <div className="w-24 text-sm text-gray-700 font-medium">{item.name}</div>
                          <div className="flex-1 h-6 bg-gray-100 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all duration-500"
                              style={{ width: `${percentage}%`, backgroundColor: RATING_COLORS[item.name] || '#6B7280' }}
                            />
                          </div>
                          <div className="w-8 text-sm text-gray-600 text-right font-semibold">{item.value}</div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* Add Custom Skill & Interested Skill Forms */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Add Custom Skill */}
              <div className="bg-white rounded-md shadow-sm p-4">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5 text-green-600">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                  </svg>
                  Add Custom Skill
                </h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Skill Name *</label>
                    <input
                      type="text"
                      value={customSkillName}
                      onChange={(e) => setCustomSkillName(e.target.value)}
                      placeholder="e.g., Machine Learning"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                    <input
                      type="text"
                      value={customSkillCategory}
                      onChange={(e) => setCustomSkillCategory(e.target.value)}
                      placeholder="e.g., Data Science"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Proficiency Level</label>
                    <select
                      value={customSkillRating}
                      onChange={(e) => setCustomSkillRating(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    >
                      <option value="Beginner">Beginner</option>
                      <option value="Developing">Developing</option>
                      <option value="Intermediate">Intermediate</option>
                      <option value="Advanced">Advanced</option>
                      <option value="Expert">Expert</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Certificate URL (Optional)</label>
                    <input
                      type="text"
                      value={customSkillCertificate}
                      onChange={(e) => setCustomSkillCertificate(e.target.value)}
                      placeholder="https://certificate-link.com"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    />
                  </div>
                  <button
                    onClick={handleAddCustomSkill}
                    disabled={!customSkillName.trim() || addingCustomSkill}
                    className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm"
                  >
                    {addingCustomSkill ? 'Adding...' : 'Add Custom Skill'}
                  </button>
                </div>

                {/* Existing Custom Skills */}
                {skills.filter(s => !s.is_interested && s.is_custom).length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <h4 className="text-sm font-semibold text-gray-700 mb-2">Your Custom Skills ({skills.filter(s => !s.is_interested && s.is_custom).length})</h4>
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      {skills.filter(s => !s.is_interested && s.is_custom).map((skill) => (
                        <div key={skill.id} className="flex items-center justify-between p-2 bg-green-50 rounded-md">
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium text-gray-900 truncate">{skill.skill?.name}</div>
                            {skill.skill?.category && <div className="text-xs text-green-700">{skill.skill.category}</div>}
                          </div>
                          <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${getSkillLevelColor(skill.rating || undefined)}`}>
                            {skill.rating || 'N/A'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Add Interested Skill */}
              <div className="bg-white rounded-md shadow-sm p-4">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5 text-blue-600">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
                  </svg>
                  Add Interested Skill
                </h3>
                <p className="text-sm text-gray-500 mb-4">Add skills you want to learn or develop</p>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Skill Name *</label>
                    <input
                      type="text"
                      value={interestedSkillName}
                      onChange={(e) => setInterestedSkillName(e.target.value)}
                      placeholder="e.g., Kubernetes"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                    <input
                      type="text"
                      value={interestedSkillCategory}
                      onChange={(e) => setInterestedSkillCategory(e.target.value)}
                      placeholder="e.g., DevOps"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <button
                    onClick={handleAddInterestedSkill}
                    disabled={!interestedSkillName.trim() || addingInterestedSkill}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm"
                  >
                    {addingInterestedSkill ? 'Adding...' : 'Add to Interests'}
                  </button>
                </div>

                {/* Existing Interested Skills */}
                {skills.filter(s => s.is_interested).length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <h4 className="text-sm font-semibold text-gray-700 mb-2">Your Interested Skills ({skills.filter(s => s.is_interested).length})</h4>
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      {skills.filter(s => s.is_interested).map((skill) => (
                        <div key={skill.id} className="flex items-center justify-between p-2 bg-blue-50 rounded-md">
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium text-gray-900 truncate">{skill.skill?.name}</div>
                            {skill.skill?.category && <div className="text-xs text-blue-700">{skill.skill.category}</div>}
                          </div>
                          <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full text-xs font-semibold">
                            Interested
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Career Engagement Tab */}
        {activeTab === 'career' && (
          <div className="space-y-6">
            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
              <div className="bg-white rounded-md shadow-sm p-3">
                <div className="text-xs text-gray-500 uppercase mb-1">Band</div>
                <div className="text-xl font-bold text-blue-600">{analysis?.band || 'L1'}</div>
              </div>
              <div className="bg-white rounded-md shadow-sm p-3">
                <div className="text-xs text-gray-500 uppercase mb-1">Average Rating</div>
                <div className="text-xl font-bold text-gray-900">{analysis?.average_rating.toFixed(2) || '0.00'}</div>
              </div>
              <div className="bg-white rounded-md shadow-sm p-3">
                <div className="text-xs text-gray-500 uppercase mb-1">Total Skills</div>
                <div className="text-xl font-bold text-gray-900">{analysis?.total_skills || 0}</div>
              </div>
              <div className="bg-white rounded-md shadow-sm p-3">
                <div className="text-xs text-gray-500 uppercase mb-1">Skills Below</div>
                <div className="text-xl font-bold text-yellow-600">{analysis?.skills_below_requirement || 0}</div>
              </div>
            </div>

            {/* Full Skill Gap Analysis Table */}
            <div className="bg-white rounded-md shadow-sm overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-200">
                <h3 className="text-lg font-bold text-gray-900">Skill Gap Analysis</h3>
              </div>

              {/* Filter Buttons */}
              <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex gap-2">
                <button
                  onClick={() => setFilter('all')}
                  className={`px-3 py-1.5 rounded-md font-medium text-sm ${
                    filter === 'all' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 border border-gray-300'
                  }`}
                >
                  All ({analysis?.skill_gaps.length || 0})
                </button>
                <button
                  onClick={() => setFilter('below')}
                  className={`px-3 py-1.5 rounded-md font-medium text-sm ${
                    filter === 'below' ? 'bg-yellow-600 text-white' : 'bg-white text-gray-700 border border-gray-300'
                  }`}
                >
                  Below Requirement ({analysis?.skills_below_requirement || 0})
                </button>
                <button
                  onClick={() => setFilter('at')}
                  className={`px-3 py-1.5 rounded-md font-medium text-sm ${
                    filter === 'at' ? 'bg-gray-600 text-white' : 'bg-white text-gray-700 border border-gray-300'
                  }`}
                >
                  At Requirement ({analysis?.skills_at_requirement || 0})
                </button>
                <button
                  onClick={() => setFilter('above')}
                  className={`px-3 py-1.5 rounded-md font-medium text-sm ${
                    filter === 'above' ? 'bg-green-600 text-white' : 'bg-white text-gray-700 border border-gray-300'
                  }`}
                >
                  Above Requirement ({analysis?.skills_above_requirement || 0})
                </button>
              </div>

              {/* Rows per page */}
              <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <label className="text-sm font-medium text-gray-700">Rows per page:</label>
                  <select
                    value={rowsPerPage}
                    onChange={(e) => setRowsPerPage(Number(e.target.value))}
                    className="px-2 py-1 border border-gray-300 rounded-md bg-white text-sm"
                  >
                    <option value={5}>5</option>
                    <option value={10}>10</option>
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                  </select>
                </div>
                <span className="text-sm text-gray-600">
                  Showing {((currentPage - 1) * rowsPerPage) + 1} to {Math.min(currentPage * rowsPerPage, filteredGaps.length)} of {filteredGaps.length} skills
                </span>
              </div>
              
              {loading ? (
                <div className="text-center py-12 text-gray-500">Loading analysis...</div>
              ) : !analysis || analysis.skill_gaps.length === 0 ? (
                <div className="text-center py-12 text-gray-500">No skill gaps found.</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-600 uppercase">Skill</th>
                        <th className="px-3 py-2 text-center text-xs font-medium text-gray-600 uppercase">Current Rating</th>
                        <th className="px-3 py-2 text-center text-xs font-medium text-gray-600 uppercase">Current Level</th>
                        <th className="px-3 py-2 text-center text-xs font-medium text-gray-600 uppercase">Required Rating<br/>({analysis.band})</th>
                        <th className="px-3 py-2 text-center text-xs font-medium text-gray-600 uppercase">Required Level</th>
                        <th className="px-3 py-2 text-center text-xs font-medium text-gray-600 uppercase">Gap</th>
                        <th className="px-3 py-2 text-center text-xs font-medium text-gray-600 uppercase min-w-[220px]">Plan to Close</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {paginatedGaps.map((gap, index) => (
                        <tr key={gap.skill_id} className={`hover:bg-gray-50 ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                          <td className="px-3 py-3 font-semibold text-gray-900">
                            <div className="text-sm">{gap.skill_name}</div>
                            {gap.skill_category && (
                              <div className="text-xs text-gray-400 mt-1">({gap.skill_category})</div>
                            )}
                          </td>
                          <td className="px-3 py-3 text-center">
                            {gap.current_rating_text ? (
                              <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold ${getSkillLevelColor(gap.current_rating_text)}`}>
                                {gap.current_rating_text}
                              </span>
                            ) : (
                              <span className="text-gray-400 text-xs">Not assessed</span>
                            )}
                          </td>
                          <td className="px-3 py-3 text-center text-sm font-medium text-gray-900">
                            {gap.current_rating_number ?? '-'}
                          </td>
                          <td className="px-3 py-3 text-center">
                            <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${getSkillLevelColor(gap.required_rating_text)}`}>
                              {gap.required_rating_text}
                            </span>
                          </td>
                          <td className="px-3 py-3 text-center text-sm font-medium text-gray-900">
                            {gap.required_rating_number}
                          </td>
                          <td className="px-3 py-3 text-center">
                            <span className={`inline-flex items-center justify-center w-12 h-6 rounded-md text-xs font-bold ${
                              gap.gap > 0 ? 'bg-green-100 text-green-800' : 
                              gap.gap === 0 ? 'bg-gray-100 text-gray-800' : 
                              'bg-yellow-100 text-yellow-800'
                            }`}>
                              {gap.gap > 0 ? `+${gap.gap}` : gap.gap}
                            </span>
                          </td>
                          <td className="px-3 py-3">
                            {gap.gap < 0 ? (
                              <input
                                type="text"
                                value={planToClose[gap.skill_id] || gap.notes || ''}
                                onChange={(e) => handlePlanChange(gap.skill_id, e.target.value)}
                                onBlur={() => handlePlanBlur(gap.skill_id, gap.employee_skill_id)}
                                placeholder="Enter your plan..."
                                className="w-full px-2 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                              />
                            ) : (
                              <span className="text-gray-400 text-sm text-center block">-</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
                  <div className="text-sm text-gray-600">
                    Page {currentPage} of {totalPages}
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      className={`px-3 py-1.5 rounded-md text-sm ${
                        currentPage === 1
                          ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                          : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                      }`}
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      className={`px-3 py-1.5 rounded-md text-sm ${
                        currentPage === totalPages
                          ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                          : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                      }`}
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Mandatory Learning Tab */}
        {activeTab === 'learning' && (
          <div className="space-y-6">
            {pendingCourses > 0 && (
              <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-yellow-700">
                      You have <strong>{pendingCourses}</strong> pending course{pendingCourses !== 1 ? 's' : ''} to complete.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {loading ? (
              <div className="text-center py-12 text-gray-500">Loading courses...</div>
            ) : assignments.length === 0 ? (
              <div className="text-center py-12 text-gray-500 bg-white rounded-lg">
                No courses assigned yet.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {assignments.map((assignment) => (
                  <div key={assignment.id} className="bg-white rounded-md shadow-sm p-4 border border-gray-200">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="text-base font-bold text-gray-900">{assignment.course_title}</h3>
                      <span className={`px-2 py-0.5 text-xs font-medium rounded ${getStatusColor(assignment.status)}`}>
                        {assignment.status}
                      </span>
                    </div>

                    {assignment.due_date && (
                      <p className="text-sm text-gray-600 mb-3">
                        Due: {new Date(assignment.due_date).toLocaleDateString()}
                      </p>
                    )}

                    {assignment.status === 'Not Started' && (
                      <button
                        onClick={() => navigate('/learning')}
                        className="w-full px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
                      >
                        Start Course
                      </button>
                    )}

                    {assignment.status === 'In Progress' && (
                      <button
                        onClick={() => navigate('/learning')}
                        className="w-full px-3 py-1.5 bg-purple-600 text-white rounded-md hover:bg-purple-700 font-medium"
                      >
                        Continue Learning
                      </button>
                    )}

                    {assignment.status === 'Completed' && (
                      <div className="text-sm text-green-600 font-medium">
                        ✓ Completed on {assignment.completed_at ? new Date(assignment.completed_at).toLocaleDateString() : 'N/A'}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            <div className="flex justify-center">
              <button
                onClick={() => navigate('/learning')}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
              >
                View All Courses
              </button>
            </div>
          </div>
        )}
      </div>


    </div>
  );
};
