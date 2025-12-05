/** Skill Gap Board - Display skills with gaps from band requirements. */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi, bandsApi, userSkillsApi, BandAnalysis, SkillGap } from '../services/api';
import NxzenLogo from '../images/Nxzen.jpg';


export const SkillGapBoard: React.FC = () => {
  const [analysis, setAnalysis] = useState<BandAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'below' | 'at' | 'above'>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [planToClose, setPlanToClose] = useState<Record<number, string>>({});
  const [targetDates, setTargetDates] = useState<Record<number, string>>({});
  const [editingSkill, setEditingSkill] = useState<number | null>(null);
  const navigate = useNavigate();
  const user = authApi.getUser();

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    loadBandAnalysis();
  }, []);

  const loadBandAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await bandsApi.getMyAnalysis();
      setAnalysis(data);
      
      // Load existing plans and dates from notes
      const plans: Record<number, string> = {};
      const dates: Record<number, string> = {};
      data.skill_gaps.forEach((gap: SkillGap) => {
        if (gap.notes) {
          // Try to parse notes as JSON to extract plan and date
          try {
            const parsed = JSON.parse(gap.notes);
            if (parsed.plan) plans[gap.skill_id] = parsed.plan;
            if (parsed.targetDate) dates[gap.skill_id] = parsed.targetDate;
          } catch {
            // If not JSON, treat as plain text plan
            plans[gap.skill_id] = gap.notes;
          }
        }
      });
      setPlanToClose(plans);
      setTargetDates(dates);
    } catch (err) {
      console.error('Failed to load band analysis:', err);
      setError(err instanceof Error ? err.message : 'Failed to load band analysis');
    } finally {
      setLoading(false);
    }
  };

  const getGapColor = (gap: number) => {
    if (gap > 0) {
      return 'bg-green-100 text-green-800'; // Above requirement
    } else if (gap === 0) {
      return 'bg-gray-100 text-gray-800'; // At requirement
    } else {
      return 'bg-yellow-100 text-yellow-800'; // Below requirement
    }
  };

  const getRatingColor = (rating?: string) => {
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

  const filteredGaps = analysis?.skill_gaps.filter((gap: SkillGap) => {
    if (filter === 'below') return gap.gap < 0;
    if (filter === 'at') return gap.gap === 0;
    if (filter === 'above') return gap.gap > 0;
    return true;
  }) || [];

  // Reset to page 1 when filter changes
  useEffect(() => {
    setCurrentPage(1);
  }, [filter]);

  // Calculate pagination
  const totalPages = Math.ceil(filteredGaps.length / rowsPerPage);
  const startIndex = (currentPage - 1) * rowsPerPage;
  const endIndex = startIndex + rowsPerPage;
  const paginatedGaps = filteredGaps.slice(startIndex, endIndex);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handleRowsPerPageChange = (newRowsPerPage: number) => {
    setRowsPerPage(newRowsPerPage);
    setCurrentPage(1); // Reset to first page when changing rows per page
  };

  const handlePlanChange = (skillId: number, value: string) => {
    setPlanToClose(prev => ({
      ...prev,
      [skillId]: value
    }));
  };

  const handlePlanBlur = async (skillId: number, employeeSkillId: number) => {
    const plan = planToClose[skillId];
    const targetDate = targetDates[skillId];
    
    try {
      // Save plan and target date as JSON in notes field
      const notesData = JSON.stringify({
        plan: plan || '',
        targetDate: targetDate || ''
      });
      
      await userSkillsApi.updateMySkill(employeeSkillId, {
        notes: notesData
      });
      
      // Exit edit mode
      setEditingSkill(null);
    } catch (err) {
      console.error('Failed to save plan:', err);
      // Optionally show error to user
    }
  };

  const handleDateChange = (skillId: number, date: string) => {
    setTargetDates(prev => ({
      ...prev,
      [skillId]: date
    }));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F6F2F4] flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl text-gray-600">Loading skill gap analysis...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#F6F2F4] flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl text-red-600 mb-4">Error: {error}</div>
          <button
            onClick={loadBandAnalysis}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="min-h-screen bg-[#F6F2F4] flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl text-gray-600">No analysis data available</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F6F2F4]">
      <header className="bg-[#F6F2F4] shadow-sm border-b border-gray-200">
        <div className="w-full px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <img src={NxzenLogo} alt="Nxzen" className="h-8 w-8 object-cover" />
            <span className="text-xl font-semibold text-gray-800">nxzen</span>
            <span aria-hidden className="h-6 w-px bg-gray-300" />
            <h1 className="text-2xl font-bold text-gray-800 italic">Profile</h1>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-200">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-gray-700">
                <path fillRule="evenodd" d="M12 2a5 5 0 100 10 5 5 0 000-10zm-7 18a7 7 0 1114 0H5z" clipRule="evenodd" />
              </svg>
              <div className="text-sm font-medium text-gray-800">
                {((user as any)?.first_name && (user as any)?.last_name)
                  ? `${(user as any).first_name} ${(user as any).last_name}`
                  : (user?.email ? user.email.split('@')[0] : 'User')}
               <br />
              <span className="text-xs text-gray-500">{user?.email}</span>
            </div>
             </div>
            <button
              onClick={() => { authApi.logout(); navigate('/login'); }}
              title="Logout"
              className="p-2 rounded-lg hover:bg-gray-200"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-red-600">
                <path d="M16 13v-2H7V8l-5 4 5 4v-3h9zm3-11H9c-1.1 0-2 .9-2 2v3h2V4h10v16H9v-2H7v3c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-6">
        <div className="flex justify-end items-center gap-2 mb-4">
          <button
            onClick={() => navigate('/learning')}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            My Learning
          </button>
          <button
            onClick={() => navigate('/dashboard')}
            className="px-4 py-2 bg-[#AD96DC] text-white rounded-lg hover:bg-[#AD96DC]-700 transition-colors"
          >
           Skills
          </button>
        </div>
        {/* Summary Card */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6 border border-gray-200">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="flex flex-col">
              <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Employee</div>
              <div className="text-lg font-bold text-gray-900">{analysis.employee_name}</div>
            </div>
            <div className="flex flex-col">
              <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Band</div>
              <div className="text-lg font-bold text-blue-600">{analysis.band}</div>
            </div>
            <div className="flex flex-col">
              <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Total Skills</div>
              <div className="text-lg font-bold text-gray-900">{analysis.total_skills}</div>
            </div>
            <div className="flex flex-col">
              <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Skills Below</div>
              <div className="text-lg font-bold text-yellow-600">{analysis.skills_below_requirement}</div>
            </div>
          </div>
        </div>

        {/* Filter Buttons */}
        <div className="mb-6 flex flex-wrap gap-3">
          <button
            onClick={() => setFilter('all')}
            className={`px-5 py-2.5 rounded-lg font-semibold transition-all shadow-sm ${
              filter === 'all' 
                ? 'bg-blue-600 text-white shadow-md scale-105' 
                : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
            }`}
          >
            All ({analysis.skill_gaps.length})
          </button>
          <button
            onClick={() => setFilter('below')}
            className={`px-5 py-2.5 rounded-lg font-semibold transition-all shadow-sm ${
              filter === 'below' 
                ? 'bg-yellow-600 text-white shadow-md scale-105' 
                : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
            }`}
          >
            Below Requirement ({analysis.skills_below_requirement})
          </button>
          <button
            onClick={() => setFilter('at')}
            className={`px-5 py-2.5 rounded-lg font-semibold transition-all shadow-sm ${
              filter === 'at' 
                ? 'bg-gray-600 text-white shadow-md scale-105' 
                : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
            }`}
          >
            At Requirement ({analysis.skills_at_requirement})
          </button>
          <button
            onClick={() => setFilter('above')}
            className={`px-5 py-2.5 rounded-lg font-semibold transition-all shadow-sm ${
              filter === 'above' 
                ? 'bg-green-600 text-white shadow-md scale-105' 
                : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
            }`}
          >
            Above Requirement ({analysis.skills_above_requirement})
          </button>
        </div>

        {/* Rows per page selector */}
        <div className="mb-4 flex justify-between items-center bg-white px-4 py-3 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center gap-3">
            <label htmlFor="rowsPerPage" className="text-sm font-medium text-gray-700">
              Rows per page:
            </label>
            <select
              id="rowsPerPage"
              value={rowsPerPage}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => handleRowsPerPageChange(Number(e.target.value))}
              className="px-3 py-2 border-2 border-gray-300 rounded-lg bg-white text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
          <span className="text-sm font-medium text-gray-600">
            Showing <span className="text-blue-600 font-bold">{startIndex + 1}</span> to <span className="text-blue-600 font-bold">{Math.min(endIndex, filteredGaps.length)}</span> of <span className="text-blue-600 font-bold">{filteredGaps.length}</span> skills
          </span>
        </div>

        {/* Skill Gap Table */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden border border-gray-200">
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="bg-gradient-to-r from-gray-50 to-gray-100 border-b-2 border-gray-300">
                  <th className="px-4 py-4 text-left text-xs font-bold text-white uppercase tracking-wider bg-black">
                    Skill
                  </th>
                  <th className="px-4 py-4 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                    Level
                  </th>
                  <th className="px-4 py-4 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                    Level
                  </th>
                  <th className="px-4 py-4 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                    Role Requirement<br/>({analysis.band})
                  </th>
                  <th className="px-4 py-4 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                    Level
                  </th>
                  <th className="px-4 py-4 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                    Gap
                  </th>
                  <th className="px-4 py-4 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider min-w-[250px]">
                    Plan to Close
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {paginatedGaps.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                      <div className="flex flex-col items-center gap-2">
                        <svg className="w-12 h-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <p className="text-lg font-medium">No skills found for the selected filter.</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  paginatedGaps.map((gap: SkillGap, index: number) => (
                    <tr 
                      key={gap.skill_id} 
                      className={`transition-colors hover:bg-blue-50 ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}
                    >
                      <td className="px-4 py-4 bg-black text-white font-semibold">
                        <div className="flex flex-col">
                          <span className="text-sm">{gap.skill_name}</span>
                          {gap.skill_category && (
                            <span className="text-xs text-gray-400 mt-1">({gap.skill_category})</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-4 text-center">
                        {gap.current_rating_text ? (
                          <span className={`inline-block px-3 py-1.5 rounded-full text-xs font-semibold ${getRatingColor(gap.current_rating_text)}`}>
                            {gap.current_rating_text}
                          </span>
                        ) : (
                          <span className="text-gray-400 text-xs italic">Not assessed</span>
                        )}
                      </td>
                      <td className="px-4 py-4 text-center text-sm font-medium text-gray-900">
                        {gap.current_rating_number ?? '-'}
                      </td>
                      <td className="px-4 py-4 text-center">
                        <span className={`inline-block px-3 py-1.5 rounded-full text-xs font-semibold ${getRatingColor(gap.required_rating_text)}`}>
                          {gap.required_rating_text}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-center text-sm font-medium text-gray-900">
                        {gap.required_rating_number}
                      </td>
                      <td className="px-4 py-4 text-center">
                        <span className={`inline-flex items-center justify-center w-16 h-8 rounded-lg text-sm font-bold ${
                          gap.gap > 0 ? 'bg-green-100 text-green-800' : 
                          gap.gap === 0 ? 'bg-gray-100 text-gray-800' : 
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {gap.gap > 0 ? `+${gap.gap}` : gap.gap}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        {gap.gap < 0 ? (
                          <div className="flex items-start gap-2">
                            <div className="flex-1 space-y-2">
                              {editingSkill === gap.skill_id ? (
                                <>
                                  <input
                                    type="text"
                                    value={planToClose[gap.skill_id] || ''}
                                    onChange={(e) => handlePlanChange(gap.skill_id, e.target.value)}
                                    placeholder="Enter your plan..."
                                    className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                                  />
                                  <input
                                    type="date"
                                    value={targetDates[gap.skill_id] || ''}
                                    onChange={(e) => handleDateChange(gap.skill_id, e.target.value)}
                                    className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                                  />
                                </>
                              ) : (
                                <>
                                  <div className="text-sm text-gray-900">
                                    {planToClose[gap.skill_id] || <span className="text-gray-400 italic">No plan set</span>}
                                  </div>
                                  {targetDates[gap.skill_id] && (
                                    <div className="text-xs text-gray-600 flex items-center gap-1">
                                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-3 h-3">
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
                                      </svg>
                                      Target: {new Date(targetDates[gap.skill_id]).toLocaleDateString()}
                                    </div>
                                  )}
                                </>
                              )}
                            </div>
                            <div className="flex flex-col gap-1">
                              {editingSkill === gap.skill_id ? (
                                <button
                                  onClick={() => handlePlanBlur(gap.skill_id, gap.employee_skill_id)}
                                  className="p-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                                  title="Save"
                                >
                                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                  </svg>
                                </button>
                              ) : (
                                <button
                                  onClick={() => setEditingSkill(gap.skill_id)}
                                  className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                                  title="Edit"
                                >
                                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                                  </svg>
                                </button>
                              )}
                            </div>
                          </div>
                        ) : (
                          <span className="text-gray-400 text-sm text-center block">-</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div className="mt-4 flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Page {currentPage} of {totalPages}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  currentPage === 1
                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                }`}
              >
                Previous
              </button>
              
              {/* Page Numbers */}
              <div className="flex items-center gap-1">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
                  // Show first page, last page, current page, and pages around current
                  if (
                    page === 1 ||
                    page === totalPages ||
                    (page >= currentPage - 1 && page <= currentPage + 1)
                  ) {
                    return (
                      <button
                        key={page}
                        onClick={() => handlePageChange(page)}
                        className={`px-3 py-2 rounded-lg transition-colors ${
                          currentPage === page
                            ? 'bg-blue-600 text-white'
                            : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                        }`}
                      >
                        {page}
                      </button>
                    );
                  } else if (
                    page === currentPage - 2 ||
                    page === currentPage + 2
                  ) {
                    return (
                      <span key={page} className="px-2 text-gray-500">
                        ...
                      </span>
                    );
                  }
                  return null;
                })}
              </div>

              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className={`px-4 py-2 rounded-lg transition-colors ${
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
  );
};

