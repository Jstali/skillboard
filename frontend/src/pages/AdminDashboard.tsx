/** Admin/HR Dashboard - View all employees, skills, and improvements. */
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { authApi, adminDashboardApi, adminApi, categoriesApi, Employee, EmployeeSkill, SkillOverview, SkillImprovement, DashboardStats, UploadResponse } from '../services/api';

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
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl text-gray-600">Loading dashboard...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">HR/Admin Dashboard</h1>
          <div className="flex gap-2 items-center">
            <span className="text-sm text-gray-600">{user?.email}</span>
            <button
              onClick={() => navigate('/dashboard')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              My Dashboard
            </button>
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
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-8">
            {(['overview', 'employees', 'skills', 'improvements'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
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
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500">Total Employees</h3>
              <p className="text-3xl font-bold text-gray-900 mt-2">{stats.total_employees}</p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500">Total Skills</h3>
              <p className="text-3xl font-bold text-gray-900 mt-2">{stats.total_skills}</p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500">Employees with Skills</h3>
              <p className="text-3xl font-bold text-gray-900 mt-2">{stats.employees_with_existing_skills}</p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500">Total Mappings</h3>
              <p className="text-3xl font-bold text-gray-900 mt-2">{stats.total_skill_mappings}</p>
            </div>
          </div>
        )}

        {activeTab === 'overview' && stats && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
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
              </div>
            ) : loading ? (
              <div className="text-center py-8 text-gray-500">Loading employees...</div>
            ) : (
              <div className="bg-white rounded-lg shadow overflow-hidden">
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
              </div>
            )}
          </div>
        )}

        {/* Skills Tab */}
        {activeTab === 'skills' && (
          <div>
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
              </div>
            )}
          </div>
        )}

        {/* Improvements Tab */}
        {activeTab === 'improvements' && (
          <div>
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
                      improvements.map((imp, idx) => (
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

