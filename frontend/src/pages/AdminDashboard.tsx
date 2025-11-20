/** Admin/HR Dashboard - View all employees, skills, and improvements. */
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { authApi, adminDashboardApi, adminApi, categoriesApi, Employee, EmployeeSkill, SkillOverview, SkillImprovement, DashboardStats, UploadResponse } from '../services/api';
import NxzenLogo from '../images/Nxzen.jpg';

export const AdminDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'employees' | 'skills' | 'improvements'>('overview');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [skillsOverview, setSkillsOverview] = useState<SkillOverview[]>([]);
  const [improvements, setImprovements] = useState<SkillImprovement[]>([]);
  const [selectedEmployee, setSelectedEmployee] = useState<string | null>(null);
  const [employeeSkills, setEmployeeSkills] = useState<EmployeeSkill[]>([]);
  const [loading, setLoading] = useState(true);
  const [departmentFilter, setDepartmentFilter] = useState<string>('');
  const [employeeSearchQuery, setEmployeeSearchQuery] = useState<string>('');
  const [skillSearchQuery, setSkillSearchQuery] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [skillCategoryFilter, setSkillCategoryFilter] = useState<string>('');
  const [employeeCategories, setEmployeeCategories] = useState<string[]>([]);
  const [skillCategories, setSkillCategories] = useState<string[]>([]);
  const [uploadingSkills, setUploadingSkills] = useState(false);
  const [skillsUploadResult, setSkillsUploadResult] = useState<UploadResponse | null>(null);
  const [uploadError, setUploadError] = useState<string>('');
  const [searchCriteria, setSearchCriteria] = useState<Array<{skill_name: string, rating: string}>>([
    { skill_name: '', rating: '' }
  ]);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [searching, setSearching] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const user = authApi.getUser();
  
  const [employeesPage, setEmployeesPage] = useState<number>(1);
  const [employeesPerPage, setEmployeesPerPage] = useState<number>(10);
  const [skillsPage, setSkillsPage] = useState<number>(1);
  const [skillsPerPage, setSkillsPerPage] = useState<number>(10);
  const [imprPage, setImprPage] = useState<number>(1);
  const [imprPerPage, setImprPerPage] = useState<number>(10);

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    loadDashboardData();
    // Load employee categories when switching to skills tab
    if (activeTab === 'skills') {
      loadEmployeeCategories();
    }
  }, [activeTab, departmentFilter, categoryFilter, skillCategoryFilter]);  // Reload when filters change

  // Load skill categories when employee category changes
  useEffect(() => {
    if (activeTab === 'skills' && categoryFilter) {
      loadSkillCategories(categoryFilter);
    } else {
      setSkillCategories([]);
      setSkillCategoryFilter(''); // Reset skill category filter when employee category changes
    }
  }, [categoryFilter, activeTab]);

  useEffect(() => {
    setEmployeesPage(1);
  }, [employeeSearchQuery, departmentFilter, isSearchMode]);

  useEffect(() => {
    setSkillsPage(1);
  }, [skillSearchQuery, categoryFilter, skillCategoryFilter]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'overview') {
        const statsData = await adminDashboardApi.getDashboardStats();
        setStats(statsData);
      } else if (activeTab === 'employees') {
        const employeesData = await adminDashboardApi.getEmployees(0, 1000, departmentFilter || undefined);
        setEmployees(employeesData);
      } else if (activeTab === 'skills') {
        const skillsData = await adminDashboardApi.getSkillsOverview(
          categoryFilter || undefined,
          skillCategoryFilter || undefined
        );
        setSkillsOverview(skillsData);
      } else if (activeTab === 'improvements') {
        const improvementsData = await adminDashboardApi.getSkillImprovements();
        setImprovements(improvementsData.improvements);
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleViewEmployeeSkills = async (employeeId: string) => {
    try {
      const skills = await adminDashboardApi.getEmployeeSkills(employeeId);
      setEmployeeSkills(skills);
      setSelectedEmployee(employeeId);
    } catch (error) {
      console.error('Failed to load employee skills:', error);
    }
  };

  const loadEmployeeCategories = async () => {
    try {
      const categories = await categoriesApi.getAll();
      setEmployeeCategories(categories);
    } catch (error) {
      console.error('Failed to load employee categories:', error);
    }
  };

  const loadSkillCategories = async (employeeCategory: string) => {
    try {
      const skillCats = await categoriesApi.getSkillCategories(employeeCategory);
      setSkillCategories(skillCats);
    } catch (error) {
      console.error('Failed to load skill categories:', error);
      setSkillCategories([]);
    }
  };

  const handleSkillSearch = async () => {
    // Filter out empty criteria
    const validCriteria = searchCriteria.filter(
      c => c.skill_name.trim() !== ''
    ).map(c => ({
      skill_name: c.skill_name.trim(),
      rating: c.rating || undefined
    }));

    if (validCriteria.length === 0) {
      // Reset to normal view if no valid criteria
      setIsSearchMode(false);
      setSearchResults([]);
      loadDashboardData();
      return;
    }

    setSearching(true);
    setIsSearchMode(true);
    try {
      const results = await adminDashboardApi.searchEmployeesBySkill(validCriteria);
      setSearchResults(results.employees);
    } catch (error) {
      console.error('Failed to search employees:', error);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleClearSearch = () => {
    setSearchCriteria([{ skill_name: '', rating: '' }]);
    setIsSearchMode(false);
    setSearchResults([]);
    loadDashboardData();
  };

  const addCriterion = () => {
    setSearchCriteria([...searchCriteria, { skill_name: '', rating: '' }]);
  };

  const removeCriterion = (index: number) => {
    if (searchCriteria.length > 1) {
      setSearchCriteria(searchCriteria.filter((_, i) => i !== index));
    }
  };

  const updateCriterion = (index: number, field: 'skill_name' | 'rating', value: string) => {
    const updated = [...searchCriteria];
    updated[index] = { ...updated[index], [field]: value };
    setSearchCriteria(updated);
  };

  const getMatchColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-green-500';
    if (percentage >= 75) return 'bg-blue-500';
    if (percentage >= 60) return 'bg-yellow-500';
    return 'bg-orange-500';
  };

  const handleLogout = () => {
    authApi.logout();
    navigate('/login');
  };

  const handleImportSkillsClick = () => {
    fileInputRef.current?.click();
  };

  const handleSkillsFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadingSkills(true);
    setUploadError('');
    setSkillsUploadResult(null);

    try {
      const result = await adminApi.uploadSkills(file);
      setSkillsUploadResult(result);
      // Reload skills overview if on skills tab
      if (activeTab === 'skills') {
        loadDashboardData();
      }
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Failed to upload skills file');
    } finally {
      setUploadingSkills(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  if (loading && activeTab === 'overview') {
    return (
      <div className="min-h-screen bg-[#F6F2F4] flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl text-gray-600">Loading dashboard...</div>
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
            <h1 className="text-2xl font-bold text-gray-800 italic">HR/Admin Dashboard</h1>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-200">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-gray-700">
                <path fillRule="evenodd" d="M12 2a5 5 0 100 10 5 5 0 000-10zm-7 18a7 7 0 1114 0H5z" clipRule="evenodd" />
              </svg>
              <div className="text-sm font-medium text-gray-800">
                {((user as any)?.first_name && (user as any)?.last_name)
                  ? `${(user as any).first_name} ${(user as any).last_name}`
                  : (user?.employee_id || (user?.email ? user.email.split('@')[0] : 'User'))}
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

      <div className="max-w-6xl mx-auto px-6 mt-4">
        <h2 className="text-center text-lg font-semibold text-gray-800 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <button
            onClick={() => setActiveTab('overview')}
            className={`flex items-center gap-3 rounded-2xl shadow-xl hover:shadow-2xl p-4 transition ${
              activeTab === 'overview' ? 'ring-2 ring-blue-500 bg-white' : 'bg-white'
            }`}
          >
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-blue-600">
                <rect x="4" y="4" width="6" height="6" rx="1"></rect>
                <rect x="14" y="4" width="6" height="6" rx="1"></rect>
                <rect x="4" y="14" width="6" height="6" rx="1"></rect>
                <rect x="14" y="14" width="6" height="6" rx="1"></rect>
              </svg>
            </span>
            <div>
              <div className="text-sm font-semibold text-gray-900">Overview</div>
              <div className="text-xs text-gray-500">Summary metrics</div>
            </div>
          </button>
          <div
            className="flex items-center gap-3 rounded-2xl shadow-xl p-4 bg-white"
            aria-label="Skill Gap Analysis"
            title="Skill Gap Analysis"
          >
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-rose-50">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-rose-600">
                <path d="M3 12c3-5 6-7 9-7s6 2 9 7"></path>
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M15 15l4 4"></path>
              </svg>
            </span>
            <div>
              <div className="text-sm font-semibold text-gray-900">Skill Gap Analysis</div>
              <div className="text-xs text-gray-500">Analyze gaps</div>
            </div>
          </div>
          <button
            onClick={() => setActiveTab('employees')}
            className={`flex items-center gap-3 rounded-2xl shadow-xl hover:shadow-2xl p-4 transition ${
              activeTab === 'employees' ? 'ring-2 ring-green-500 bg-white' : 'bg-white'
            }`}
          >
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-green-50">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-green-600">
                <circle cx="8" cy="9" r="3"></circle>
                <circle cx="16" cy="9" r="3"></circle>
                <path d="M2 20c0-3.5 3.5-6 8-6s8 2.5 8 6"></path>
              </svg>
            </span>
            <div>
              <div className="text-sm font-semibold text-gray-900">Employees</div>
              <div className="text-xs text-gray-500">Manage employees</div>
            </div>
          </button>
          <button
            onClick={() => setActiveTab('skills')}
            className={`flex items-center gap-3 rounded-2xl shadow-xl hover:shadow-2xl p-4 transition ${
              activeTab === 'skills' ? 'ring-2 ring-purple-500 bg-white' : 'bg-white'
            }`}
          >
            <span className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-purple-100">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" className="w-8 h-8 text-purple-700">
                <path fill="currentColor" d="M12 2c4.97 0 9 3.58 9 8.3 0 3.73-2.65 6.93-6.25 7.67V21H9.5v-2.06C6.07 18.4 3 15.15 3 10.96 3 5.66 7.03 2 12 2z"/>
                <g fill="#ffffff">
                  <circle cx="12" cy="11" r="2"/>
                  <rect x="11.3" y="6.5" width="1.4" height="2.2" rx="0.3"/>
                  <rect x="15.8" y="10.3" width="2.2" height="1.4" rx="0.3"/>
                  <rect x="11.3" y="13.3" width="1.4" height="2.2" rx="0.3"/>
                  <rect x="6" y="10.3" width="2.2" height="1.4" rx="0.3"/>
                  <rect x="14.7" y="8" width="1.6" height="1.6" rx="0.3"/>
                  <rect x="8.7" y="8" width="1.6" height="1.6" rx="0.3"/>
                  <rect x="14.7" y="12.9" width="1.6" height="1.6" rx="0.3"/>
                  <rect x="8.7" y="12.9" width="1.6" height="1.6" rx="0.3"/>
                </g>
              </svg>
            </span>
            <div>
              <div className="text-sm font-semibold text-gray-900">Skills</div>
              <div className="text-xs text-gray-500">Browse skills</div>
            </div>
          </button>
          <button
            onClick={() => setActiveTab('improvements')}
            className={`flex items-center gap-3 rounded-2xl shadow-xl hover:shadow-2xl p-4 transition ${
              activeTab === 'improvements' ? 'ring-2 ring-indigo-500 bg-white' : 'bg-white'
            }`}
          >
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-indigo-600">
                <path d="M6 18v-4"></path>
                <path d="M12 18v-7"></path>
                <path d="M18 18v-10"></path>
                <path d="M5 6l5 5 4-3 5 5"></path>
              </svg>
            </span>
            <div>
              <div className="text-sm font-semibold text-gray-900">Improvements</div>
              <div className="text-xs text-gray-500">Track improvements</div>
            </div>
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Upload Result Messages */}
        {uploadError && (
          <div className="mb-4 rounded-md bg-red-50 p-4">
            <div className="text-sm text-red-800">{uploadError}</div>
          </div>
        )}
        {skillsUploadResult && (
          <div className="mb-4 rounded-md bg-green-50 p-4">
            <p className="text-sm font-semibold text-green-800">{skillsUploadResult.message}</p>
            <p className="text-xs text-green-600 mt-2">
              Processed: {skillsUploadResult.rows_processed} | 
              Created: {skillsUploadResult.rows_created} | 
              Updated: {skillsUploadResult.rows_updated}
            </p>
            {skillsUploadResult.errors && skillsUploadResult.errors.length > 0 && (
              <div className="mt-2">
                <p className="text-xs font-semibold text-red-600">Errors:</p>
                <ul className="text-xs text-red-600 list-disc list-inside">
                  {skillsUploadResult.errors.slice(0, 5).map((err, idx) => (
                    <li key={idx}>{err}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Overview Tab */}
        {activeTab === 'overview' && stats && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
              <h3 className="text-sm font-medium text-gray-500">Total Employees</h3>
              <p className="text-3xl font-bold text-gray-900 mt-2">{stats.total_employees}</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
              <h3 className="text-sm font-medium text-gray-500">Total Skills</h3>
              <p className="text-3xl font-bold text-gray-900 mt-2">{stats.total_skills}</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
              <h3 className="text-sm font-medium text-gray-500">Employees with Skills</h3>
              <p className="text-3xl font-bold text-gray-900 mt-2">{stats.employees_with_existing_skills}</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
              <h3 className="text-sm font-medium text-gray-500">Total Mappings</h3>
              <p className="text-3xl font-bold text-gray-900 mt-2">{stats.total_skill_mappings}</p>
            </div>
          </div>
        )}

        {activeTab === 'overview' && stats && (
          <div className="bg-[#F6F2F4] rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Rating Breakdown</h2>
            <div className="grid grid-cols-3 gap-4">
              {Object.entries(stats.rating_breakdown).map(([rating, count]) => (
                <div key={rating} className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-gray-900">{count}</p>
                  <p className="text-sm text-gray-600">{rating}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Employees Tab */}
        {activeTab === 'employees' && (
          <div>
            {/* Skill-based Search Section */}
            <div className="mb-6 bg-blue-50 rounded-lg p-4 border border-blue-200">
              <h3 className="text-lg font-semibold mb-3 text-gray-800">Search Employees by Multiple Skills & Ratings</h3>
             
              
              <div className="space-y-3">
                {searchCriteria.map((criterion, index) => (
                  <div key={index} className="flex gap-3 items-end flex-wrap bg-white p-3 rounded-lg border border-gray-200">
                    <div className="flex-1 min-w-[200px]">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Skill Name {searchCriteria.length > 1 && `#${index + 1}`}
                      </label>
                      <input
                        type="text"
                        placeholder="e.g., policy, audit, python..."
                        value={criterion.skill_name}
                        onChange={(e) => updateCriterion(index, 'skill_name', e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSkillSearch()}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div className="min-w-[180px]">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Rating Level</label>
                      <select
                        value={criterion.rating}
                        onChange={(e) => updateCriterion(index, 'rating', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                      >
                        <option value="">All Ratings</option>
                        <option value="Beginner">Beginner</option>
                        <option value="Developing">Developing</option>
                        <option value="Intermediate">Intermediate</option>
                        <option value="Advanced">Advanced</option>
                        <option value="Expert">Expert</option>
                      </select>
                    </div>
                    {searchCriteria.length > 1 && (
                      <button
                        onClick={() => removeCriterion(index)}
                        className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 font-medium"
                        title="Remove this criterion"
                      >
                        Remove
                      </button>
                    )}
                  </div>
                ))}
                
                <div className="flex gap-2 items-center">
                  <button
                    onClick={addCriterion}
                    className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 font-medium text-sm"
                  >
                    + Add Another Skill
                  </button>
                  <button
                    onClick={handleSkillSearch}
                    disabled={searching}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                  >
                    {searching ? 'Searching...' : 'Search'}
                  </button>
                  {isSearchMode && (
                    <button
                      onClick={handleClearSearch}
                      className="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 font-medium"
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>
              
              {isSearchMode && (
                <div className="mt-3 text-sm text-gray-600">
                  Found {searchResults.length} employee{searchResults.length !== 1 ? 's' : ''} matching {searchResults[0]?.criteria_count || searchCriteria.filter(c => c.skill_name.trim()).length} criteria
                </div>
              )}
            </div>

            {/* Regular Search/Filter Section */}
            <div className="mb-4 flex gap-4 items-center flex-wrap">
              <div className="flex-1 min-w-[200px]">
                <input
                  type="text"
                  placeholder="Search employees by name, email, or ID..."
                  value={employeeSearchQuery}
                  onChange={(e) => setEmployeeSearchQuery(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="min-w-[200px]">
                <input
                  type="text"
                  placeholder="Filter by department..."
                  value={departmentFilter}
                  onChange={(e) => setDepartmentFilter(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            {searching ? (
              <div className="text-center py-8 text-gray-500">Searching employees...</div>
            ) : isSearchMode ? (
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="flex justify-end items-center gap-2 p-3">
                  <label className="text-sm text-gray-600">Rows per page</label>
                  <select
                    value={employeesPerPage}
                    onChange={(e) => { setEmployeesPerPage(Number(e.target.value)); setEmployeesPage(1); }}
                    className="px-2 py-1 border border-gray-300 rounded-lg bg-white text-sm"
                  >
                    {[5,10,20,50,100].map(n => <option key={n} value={n}>{n}</option>)}
                  </select>
                </div>
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Match %</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Employee ID</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Department</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Matching Skills</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {searchResults
                      .filter((result) => {
                        if (employeeSearchQuery) {
                          const query = employeeSearchQuery.toLowerCase();
                          const emp = result.employee;
                          return (
                            emp.name?.toLowerCase().includes(query) ||
                            emp.company_email?.toLowerCase().includes(query) ||
                            emp.employee_id?.toLowerCase().includes(query) ||
                            emp.department?.toLowerCase().includes(query) ||
                            emp.role?.toLowerCase().includes(query)
                          );
                        }
                        return true;
                      })
                      .slice((employeesPage-1)*employeesPerPage, (employeesPage-1)*employeesPerPage + employeesPerPage)
                      .map((result) => {
                        const emp = result.employee;
                        return (
                          <tr key={emp.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <div className="w-24 bg-gray-200 rounded-full h-2.5 mr-2">
                                  <div
                                    className={`h-2.5 rounded-full ${getMatchColor(result.match_percentage)}`}
                                    style={{ width: `${result.match_percentage}%` }}
                                  ></div>
                                </div>
                                <span className="text-sm font-medium text-gray-900">{result.match_percentage}%</span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{emp.employee_id}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{emp.name}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{emp.company_email || '-'}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{emp.department || '-'}</td>
                            <td className="px-6 py-4 text-sm text-gray-500">
                              <div className="space-y-1">
                                <div className="text-xs text-gray-400 mb-1">
                                  Matched {result.match_count} of {result.criteria_count} criteria
                                </div>
                                <div className="flex flex-wrap gap-1">
                                  {result.matching_skills.map((skill, idx) => (
                                    <span
                                      key={idx}
                                      className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800"
                                      title={`${skill.skill_name} - ${skill.rating} (${skill.match_score}% match)`}
                                    >
                                      {skill.skill_name} ({skill.rating})
                                    </span>
                                  ))}
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                              <button
                                onClick={() => handleViewEmployeeSkills(emp.employee_id)}
                                className="text-blue-600 hover:text-blue-800"
                              >
                                View Skills
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
                {searchResults.length === 0 && (
                  <div className="text-center py-8 text-gray-500">No employees found matching your search criteria.</div>
                )}
                <div className="flex justify-end items-center gap-2 p-3">
                  {(() => {
                    const total = searchResults.filter((result) => {
                      if (employeeSearchQuery) {
                        const query = employeeSearchQuery.toLowerCase();
                        const emp = result.employee;
                        return (
                          emp.name?.toLowerCase().includes(query) ||
                          emp.company_email?.toLowerCase().includes(query) ||
                          emp.employee_id?.toLowerCase().includes(query) ||
                          emp.department?.toLowerCase().includes(query) ||
                          emp.role?.toLowerCase().includes(query)
                        );
                      }
                      return true;
                    }).length;
                    const totalPages = Math.max(1, Math.ceil(total / employeesPerPage));
                    return (
                      <>
                        <button
                          onClick={() => setEmployeesPage(p => Math.max(1, p - 1))}
                          className="px-3 py-1 rounded bg-gray-100 hover:bg-gray-200 text-sm"
                          disabled={employeesPage <= 1}
                        >Prev</button>
                        <span className="text-sm text-gray-600">Page {employeesPage} of {totalPages}</span>
                        <button
                          onClick={() => setEmployeesPage(p => Math.min(totalPages, p + 1))}
                          className="px-3 py-1 rounded bg-gray-100 hover:bg-gray-200 text-sm"
                          disabled={employeesPage >= totalPages}
                        >Next</button>
                      </>
                    );
                  })()}
                </div>
              </div>
            ) : loading ? (
              <div className="text-center py-8 text-gray-500">Loading employees...</div>
            ) : (
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="flex justify-end items-center gap-2 p-3">
                  <label className="text-sm text-gray-600">Rows per page</label>
                  <select
                    value={employeesPerPage}
                    onChange={(e) => { setEmployeesPerPage(Number(e.target.value)); setEmployeesPage(1); }}
                    className="px-2 py-1 border border-gray-300 rounded-lg bg-white text-sm"
                  >
                    {[5,10,20,50,100].map(n => <option key={n} value={n}>{n}</option>)}
                  </select>
                </div>
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Employee ID</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Department</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {employees
                      .filter((emp) => {
                        if (employeeSearchQuery) {
                          const query = employeeSearchQuery.toLowerCase();
                          return (
                            emp.name?.toLowerCase().includes(query) ||
                            emp.company_email?.toLowerCase().includes(query) ||
                            emp.employee_id?.toLowerCase().includes(query) ||
                            emp.department?.toLowerCase().includes(query) ||
                            emp.role?.toLowerCase().includes(query)
                          );
                        }
                        return true;
                      })
                      .slice((employeesPage-1)*employeesPerPage, (employeesPage-1)*employeesPerPage + employeesPerPage)
                      .map((emp) => (
                      <tr key={emp.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{emp.employee_id}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{emp.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{emp.company_email || '-'}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{emp.department || '-'}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{emp.role || '-'}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <button
                            onClick={() => handleViewEmployeeSkills(emp.employee_id)}
                            className="text-blue-600 hover:text-blue-800"
                          >
                            View Skills
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="flex justify-end items-center gap-2 p-3">
                  {(() => {
                    const total = employees.filter((emp) => {
                      if (employeeSearchQuery) {
                        const query = employeeSearchQuery.toLowerCase();
                        return (
                          emp.name?.toLowerCase().includes(query) ||
                          emp.company_email?.toLowerCase().includes(query) ||
                          emp.employee_id?.toLowerCase().includes(query) ||
                          emp.department?.toLowerCase().includes(query) ||
                          emp.role?.toLowerCase().includes(query)
                        );
                      }
                      return true;
                    }).length;
                    const totalPages = Math.max(1, Math.ceil(total / employeesPerPage));
                    return (
                      <>
                        <button
                          onClick={() => setEmployeesPage(p => Math.max(1, p - 1))}
                          className="px-3 py-1 rounded bg-gray-100 hover:bg-gray-200 text-sm"
                          disabled={employeesPage <= 1}
                        >Prev</button>
                        <span className="text-sm text-gray-600">Page {employeesPage} of {totalPages}</span>
                        <button
                          onClick={() => setEmployeesPage(p => Math.min(totalPages, p + 1))}
                          className="px-3 py-1 rounded bg-gray-100 hover:bg-gray-200 text-sm"
                          disabled={employeesPage >= totalPages}
                        >Next</button>
                      </>
                    );
                  })()}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Skills Tab */}
        {activeTab === 'skills' && (
          <div>
            <div className="flex justify-end items-center gap-2 mb-4">
              <button
                onClick={handleImportSkillsClick}
                disabled={uploadingSkills}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploadingSkills ? 'Uploading...' : 'Import Skills'}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls,.csv"
                onChange={handleSkillsFileChange}
                className="hidden"
              />
            </div>
            <div className="mb-4 flex gap-4 items-center flex-wrap">
              <div className="flex-1 min-w-[200px]">
                <input
                  type="text"
                  placeholder="Search skills by name, category, or description..."
                  value={skillSearchQuery}
                  onChange={(e) => setSkillSearchQuery(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="min-w-[200px]">
                <select
                  value={categoryFilter}
                  onChange={(e) => {
                    setCategoryFilter(e.target.value);
                    setSkillCategoryFilter(''); // Reset skill category when employee category changes
                  }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  <option value="">All Employee Categories</option>
                  {employeeCategories.sort().map((category) => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
              </div>
              {categoryFilter && (
                <div className="min-w-[200px]">
                  <select
                    value={skillCategoryFilter}
                    onChange={(e) => setSkillCategoryFilter(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  >
                    <option value="">All Skill Categories</option>
                    {skillCategories.sort().map((skillCat) => (
                      <option key={skillCat} value={skillCat}>{skillCat}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>
            <div className="flex justify-end items-center gap-2 mb-2">
              <label className="text-sm text-gray-600">Skills per page</label>
              <select
                value={skillsPerPage}
                onChange={(e) => { setSkillsPerPage(Number(e.target.value)); setSkillsPage(1); }}
                className="px-2 py-1 border border-gray-300 rounded-lg bg-white text-sm"
              >
                {[5,10,20,50,100].map(n => <option key={n} value={n}>{n}</option>)}
              </select>
            </div>
            {loading ? (
              <div className="text-center py-8 text-gray-500">Loading skills...</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {skillsOverview
                  .filter((item) => {
                    // Category filtering is now done on the backend
                    // Only filter by search query on frontend
                    if (skillSearchQuery) {
                      const query = skillSearchQuery.toLowerCase();
                      return (
                        item.skill.name?.toLowerCase().includes(query) ||
                        item.skill.category?.toLowerCase().includes(query) ||
                        item.skill.description?.toLowerCase().includes(query)
                      );
                    }
                    return true;
                  })
                  .slice((skillsPage-1)*skillsPerPage, (skillsPage-1)*skillsPerPage + skillsPerPage)
                  .map((item) => {
                  // Prepare data for the chart
                  const chartData = [
                    {
                      rating: 'Beginner',
                      employees: item.rating_breakdown.Beginner || 0,
                    },
                    {
                      rating: 'Developing',
                      employees: item.rating_breakdown.Developing || 0,
                    },
                    {
                      rating: 'Intermediate',
                      employees: item.rating_breakdown.Intermediate || 0,
                    },
                    {
                      rating: 'Advanced',
                      employees: item.rating_breakdown.Advanced || 0,
                    },
                    {
                      rating: 'Expert',
                      employees: item.rating_breakdown.Expert || 0,
                    },
                  ];

                  return (
                    <div key={item.skill.id} className="bg-white rounded-lg shadow-md p-4">
                      <div className="mb-3">
                        <h3 className="text-base font-semibold text-gray-800">{item.skill.name}</h3>
                        {item.skill.category && (
                          <span className="inline-block mt-1 px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                            {item.skill.category}
                          </span>
                        )}
                        {item.skill.description && (
                          <p className="text-xs text-gray-600 mt-1 line-clamp-2">{item.skill.description}</p>
                        )}
                        <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-600">
                          <span>Total: <strong className="text-gray-900">{item.total_employees}</strong></span>
                          <span>Existing: <strong className="text-gray-900">{item.existing_skills_count}</strong></span>
                          <span>Interested: <strong className="text-gray-900">{item.interested_skills_count}</strong></span>
                        </div>
                      </div>
                      
                      {/* Bar Chart */}
                      <div className="mt-3">
                        <h4 className="text-xs font-medium text-gray-700 mb-2">Rating Distribution</h4>
                        <ResponsiveContainer width="100%" height={150}>
                          <BarChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis 
                              dataKey="rating" 
                              tick={{ fontSize: 10 }}
                              angle={-45}
                              textAnchor="end"
                              height={50}
                            />
                            <YAxis 
                              tick={{ fontSize: 10 }}
                              allowDecimals={false}
                              width={40}
                            />
                            <Tooltip />
                            <Bar dataKey="employees" fill="#3b82f6" name="Employees" />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  );
                })}
                
                {skillsOverview.filter((item) => {
                  // Filter by category
                  if (categoryFilter && item.skill.category !== categoryFilter) {
                    return false;
                  }
                  // Filter by search query
                  if (skillSearchQuery) {
                    const query = skillSearchQuery.toLowerCase();
                    return (
                      item.skill.name?.toLowerCase().includes(query) ||
                      item.skill.category?.toLowerCase().includes(query) ||
                      item.skill.description?.toLowerCase().includes(query)
                    );
                  }
                  return true;
                  }).length === 0 && (
                  <div className="col-span-full text-center py-8 text-gray-500">No skills found</div>
                )}
                <div className="col-span-full flex justify-end items-center gap-2">
                  {(() => {
                    const total = skillsOverview.filter((item) => {
                      if (categoryFilter && item.skill.category !== categoryFilter) return false;
                      if (skillSearchQuery) {
                        const query = skillSearchQuery.toLowerCase();
                        return (
                          item.skill.name?.toLowerCase().includes(query) ||
                          item.skill.category?.toLowerCase().includes(query) ||
                          item.skill.description?.toLowerCase().includes(query)
                        );
                      }
                      return true;
                    }).length;
                    const totalPages = Math.max(1, Math.ceil(total / skillsPerPage));
                    return (
                      <>
                        <button
                          onClick={() => setSkillsPage(p => Math.max(1, p - 1))}
                          className="px-3 py-1 rounded bg-gray-100 hover:bg-gray-200 text-sm"
                          disabled={skillsPage <= 1}
                        >Prev</button>
                        <span className="text-sm text-gray-600">Page {skillsPage} of {totalPages}</span>
                        <button
                          onClick={() => setSkillsPage(p => Math.min(totalPages, p + 1))}
                          className="px-3 py-1 rounded bg-gray-100 hover:bg-gray-200 text-sm"
                          disabled={skillsPage >= totalPages}
                        >Next</button>
                      </>
                    );
                  })()}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Improvements Tab */}
        {activeTab === 'improvements' && (
          <div>
            <div className="flex justify-end items-center mb-2">
              <label className="text-sm text-gray-600 mr-2">Rows per page</label>
              <select
                value={imprPerPage}
                onChange={(e) => { setImprPerPage(Number(e.target.value)); setImprPage(1); }}
                className="px-2 py-1 border border-gray-300 rounded-lg bg-white text-sm"
              >
                {[5,10,20,50,100].map(n => <option key={n} value={n}>{n}</option>)}
              </select>
            </div>
            {loading ? (
              <div className="text-center py-8 text-gray-500">Loading improvements...</div>
            ) : (
              <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="p-4 bg-blue-50 border-b border-blue-200">
                <p className="text-sm text-blue-800">
                  Showing only skills where employees have improved (current rating &gt; initial rating). Skills are tracked from their first rating.
                </p>
              </div>
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Employee</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Skill</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Initial Rating</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Current Rating</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Years Experience</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {improvements.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-6 py-8 text-center text-sm text-gray-500">
                          No skill improvements found. Employees need to upgrade their skill ratings to appear here.
                        </td>
                      </tr>
                    ) : (
                      improvements.slice((imprPage-1)*imprPerPage, (imprPage-1)*imprPerPage + imprPerPage).map((imp, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {imp.employee_name} ({imp.employee_id})
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{imp.skill_name}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{imp.initial_rating}</td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              {imp.current_rating}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{imp.years_experience || '-'}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
                <div className="flex justify-end items-center gap-2 p-3">
                  {(() => {
                    const total = improvements.length;
                    const totalPages = Math.max(1, Math.ceil(total / imprPerPage));
                    return (
                      <>
                        <button
                          onClick={() => setImprPage(p => Math.max(1, p - 1))}
                          className="px-3 py-1 rounded bg-gray-100 hover:bg-gray-200 text-sm"
                          disabled={imprPage <= 1}
                        >Prev</button>
                        <span className="text-sm text-gray-600">Page {imprPage} of {totalPages}</span>
                        <button
                          onClick={() => setImprPage(p => Math.min(totalPages, p + 1))}
                          className="px-3 py-1 rounded bg-gray-100 hover:bg-gray-200 text-sm"
                          disabled={imprPage >= totalPages}
                        >Next</button>
                      </>
                    );
                  })()}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Employee Skills Modal */}
        {selectedEmployee && employeeSkills.length > 0 && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto">
              <div className="p-6 border-b border-gray-200 flex justify-between items-center">
                <h2 className="text-xl font-semibold">Skills for Employee: {selectedEmployee}</h2>
                <button
                  onClick={() => {
                    setSelectedEmployee(null);
                    setEmployeeSkills([]);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  {employeeSkills.map((es) => (
                    <div key={es.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="font-semibold text-gray-900">{es.skill?.name || 'Unknown Skill'}</h3>
                          <div className="mt-2 space-y-1">
                            {es.is_interested ? (
                              <span className="inline-block px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded">Interested</span>
                            ) : (
                              <>
                                {es.rating && (
                                  <span className="inline-block px-2 py-1 bg-green-100 text-green-800 text-xs rounded mr-2">
                                    {es.rating}
                                  </span>
                                )}
                                <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">Existing</span>
                              </>
                            )}
                            {es.years_experience && (
                              <span className="text-xs text-gray-500 ml-2">{es.years_experience} years</span>
                            )}
                          </div>
                          {es.notes && (
                            <p className="text-sm text-gray-600 mt-2">{es.notes}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

