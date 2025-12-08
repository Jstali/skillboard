/** Admin/HR Dashboard - View all employees, skills, and improvements. */
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';
import { authApi, adminDashboardApi, adminApi, categoriesApi, bandsApi, skillsApi, templatesApi, learningApi, Employee, EmployeeSkill, SkillOverview, SkillImprovement, DashboardStats, UploadResponse, BandAnalysis, Course } from '../services/api';
import { Button } from '../components/Button';
import { PageHeader } from '../components/PageHeader';
import { Activity, Users, BookOpen, TrendingUp, BarChart2, Briefcase, ChevronDown, ChevronRight, Plus, Upload, Trash2, Edit2, Play, Search, Target, Award, Download, LayoutGrid, Layers } from 'lucide-react';
import { SearchableSelect } from '../components/SearchableSelect';
import { TemplateManagement } from '../components/TemplateManagement';
import { CareerPathways } from './CareerPathways';

export const AdminDashboard: React.FC = () => {
  const [searchParams] = useSearchParams();
  const initialTab = (searchParams.get('tab') as 'overview' | 'employees' | 'skills' | 'improvements' | 'skill-gap' | 'courses' | 'career-pathways') || 'overview';
  const [activeTab, setActiveTab] = useState<'overview' | 'employees' | 'skills' | 'improvements' | 'skill-gap' | 'courses' | 'career-pathways'>(initialTab);
  const [allEmployeesAnalysis, setAllEmployeesAnalysis] = useState<BandAnalysis[]>([]);
  const [loadingSkillGap, setLoadingSkillGap] = useState(false);
  const [skillGapSearchQuery, setSkillGapSearchQuery] = useState<string>('');
  const [skillGapPage, setSkillGapPage] = useState<number>(1);
  const [skillGapPerPage, setSkillGapPerPage] = useState<number>(5);
  const [adoptionSelectedSkills, setAdoptionSelectedSkills] = useState<string[]>([]);
  const [expandedEmployees, setExpandedEmployees] = useState<string[]>([]);
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
  const [searchCriteria, setSearchCriteria] = useState<Array<{ skill_name: string, rating: string }>>([
    { skill_name: '', rating: '' }
  ]);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [searching, setSearching] = useState(false);
  const [uploadingCategory, setUploadingCategory] = useState<string | null>(null);
  const [categoryTemplates, setCategoryTemplates] = useState<Record<string, any[]>>({});
  const categoryFileInputRefs = useRef<Record<string, HTMLInputElement | null>>({});
  const [showAddCategory, setShowAddCategory] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [addingCategory, setAddingCategory] = useState(false);
  const [categorySearchQuery, setCategorySearchQuery] = useState('');
  const [expandedSubcategories, setExpandedSubcategories] = useState<Record<string, boolean>>({});
  // Modal states for adding skill category and skill
  const [showAddSkillCategoryModal, setShowAddSkillCategoryModal] = useState(false);
  const [newSkillCategoryName, setNewSkillCategoryName] = useState('');
  const [addSkillCategoryForPathway, setAddSkillCategoryForPathway] = useState('');
  const [savingSkillCategory, setSavingSkillCategory] = useState(false);
  const [showAddSkillModal, setShowAddSkillModal] = useState(false);
  const [newSkillName, setNewSkillName] = useState('');
  const [addSkillForCategory, setAddSkillForCategory] = useState('');
  const [addSkillForPathway, setAddSkillForPathway] = useState('');
  const [savingSkill, setSavingSkill] = useState(false);
  // Template management states
  const [templates, setTemplates] = useState<any[]>([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [uploadingTemplate, setUploadingTemplate] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<any | null>(null);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [templateToDelete, setTemplateToDelete] = useState<number | null>(null);
  const templateFileInputRef = useRef<HTMLInputElement | null>(null);
  const navigate = useNavigate();

  const user = authApi.getUser();

  const [employeesPage, setEmployeesPage] = useState<number>(1);
  const [employeesPerPage, setEmployeesPerPage] = useState<number>(10);
  const [skillsPage, setSkillsPage] = useState<number>(1);
  const [skillsPerPage, setSkillsPerPage] = useState<number>(10);
  const [imprPage, setImprPage] = useState<number>(1);
  const [imprPerPage, setImprPerPage] = useState<number>(10);
  const [expandedImprovementEmployees, setExpandedImprovementEmployees] = useState<string[]>([]);

  // Course Management States
  const [courses, setCourses] = useState<Course[]>([]);
  const [loadingCourses, setLoadingCourses] = useState(false);
  const [showCourseModal, setShowCourseModal] = useState(false);
  const [savingCourse, setSavingCourse] = useState(false);
  const [currentCourse, setCurrentCourse] = useState<Partial<Course>>({});
  const [courseToDelete, setCourseToDelete] = useState<number | null>(null);
  const [allSimpleSkills, setAllSimpleSkills] = useState<any[]>([]); // For skill selection dropdown in course modal

  // Bulk Assignment States
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assignCourse, setAssignCourse] = useState<Course | null>(null);
  const [selectedEmployeeIds, setSelectedEmployeeIds] = useState<number[]>([]);
  const [assigning, setAssigning] = useState(false);
  const [assignmentSearchQuery, setAssignmentSearchQuery] = useState('');

  // Skills Modal States
  const [showSkillsModal, setShowSkillsModal] = useState(false);
  const [selectedEmployeeForSkills, setSelectedEmployeeForSkills] = useState<{ employee_id: string, employee_name: string, band: string, skills: any[] } | null>(null);
  const [loadingEmployeeSkills, setLoadingEmployeeSkills] = useState(false);

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

  useEffect(() => {
    setSkillGapPage(1);
  }, [skillGapSearchQuery]);

  const loadCourses = async () => {
    setLoadingCourses(true);
    try {
      const [coursesData, skillsData] = await Promise.all([
        learningApi.getAllCourses(),
        skillsApi.getAllSimple()
      ]);
      setCourses(coursesData);
      setAllSimpleSkills(skillsData);
    } catch (error) {
      console.error('Failed to load courses:', error);
    } finally {
      setLoadingCourses(false);
    }
  };

  const handleCreateCourse = () => {
    setCurrentCourse({ is_mandatory: false });
    setShowCourseModal(true);
  };

  const handleEditCourse = (course: Course) => {
    setCurrentCourse({ ...course });
    setShowCourseModal(true);
  };

  const handleSaveCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentCourse.title) return;

    setSavingCourse(true);
    try {
      await learningApi.createCourse({
        title: currentCourse.title,
        description: currentCourse.description,
        skill_id: currentCourse.skill_id,
        external_url: currentCourse.external_url,
        is_mandatory: currentCourse.is_mandatory || false
      });
      await loadCourses();
      setShowCourseModal(false);
    } catch (error) {
      console.error('Failed to save course:', error);
      alert('Failed to save course');
    } finally {
      setSavingCourse(false);
    }
  };

  const handleDeleteCourse = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this course?')) return;
    try {
      await learningApi.deleteCourse(id);
      await loadCourses();
    } catch (error) {
      console.error('Failed to delete course:', error);
      alert('Failed to delete course');
    }
  };

  const handleOpenAssignModal = (course: Course) => {
    setAssignCourse(course);
    setSelectedEmployeeIds([]);
    setAssignmentSearchQuery('');
    setAssigning(false);
    setShowAssignModal(true);
    // Ensure employees are loaded
    if (employees.length === 0) {
      adminDashboardApi.getEmployees(0, 1000).then(setEmployees);
    }
  };

  const handleAssignCourse = async () => {
    if (!assignCourse || selectedEmployeeIds.length === 0) return;

    setAssigning(true);
    try {
      await learningApi.assignCourse({
        course_id: assignCourse.id,
        employee_ids: selectedEmployeeIds
      });
      alert(`Successfully assigned "${assignCourse.title}" to ${selectedEmployeeIds.length} employees.`);
      setShowAssignModal(false);
    } catch (error) {
      console.error("Failed to assign course:", error);
      alert("Failed to assign course. Please try again.");
    } finally {
      setAssigning(false);
    }
  };

  const toggleEmployeeSelection = (employeeId: number) => {
    setSelectedEmployeeIds(prev =>
      prev.includes(employeeId)
        ? prev.filter(id => id !== employeeId)
        : [...prev, employeeId]
    );
  };

  const handleSelectAllFilteredEmployees = () => {
    const filtered = employees.filter(e =>
      e.name.toLowerCase().includes(assignmentSearchQuery.toLowerCase()) ||
      e.employee_id.toLowerCase().includes(assignmentSearchQuery.toLowerCase())
    );
    const allIds = filtered.map(e => e.id);

    // If all filtered are already selected, deselect them
    const allSelected = allIds.every(id => selectedEmployeeIds.includes(id));

    if (allSelected) {
      setSelectedEmployeeIds(prev => prev.filter(id => !allIds.includes(id)));
    } else {
      // Add missing ones
      const newIds = [...selectedEmployeeIds];
      allIds.forEach(id => {
        if (!newIds.includes(id)) newIds.push(id);
      });
      setSelectedEmployeeIds(newIds);
    }
  };

  const loadAllEmployeesAnalysis = async () => {
    setLoadingSkillGap(true);
    try {
      const analyses = await bandsApi.getAllEmployeesAnalysis();
      setAllEmployeesAnalysis(analyses);
    } catch (error) {
      console.error('Failed to load all employees analysis:', error);
    } finally {
      setLoadingSkillGap(false);
    }
  };

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'overview') {
        const statsData = await adminDashboardApi.getDashboardStats();
        setStats(statsData);
        const skillsData = await adminDashboardApi.getSkillsOverview(undefined, undefined);
        setSkillsOverview(skillsData);
        const initialTop5 = skillsData
          .map(s => ({ name: s.skill.name, total: (s.existing_skills_count || 0) + (s.interested_skills_count || 0) }))
          .sort((a, b) => b.total - a.total)
          .slice(0, 10)
          .map(s => s.name);
        setAdoptionSelectedSkills(initialTop5);
        try {
          const analyses = await bandsApi.getAllEmployeesAnalysis();
          setAllEmployeesAnalysis(analyses);
        } catch (e) { }
      } else if (activeTab === 'employees') {
        const employeesData = await adminDashboardApi.getEmployees(0, 1000, departmentFilter || undefined);
        setEmployees(employeesData);
      } else if (activeTab === 'courses') {
        await loadCourses();
      } else if (activeTab === 'skills') {
        // Load category templates
        const categories = await categoriesApi.getAll();
        setEmployeeCategories(categories);

        // Load templates with stats for each category
        const templates: Record<string, any[]> = {};
        for (const category of categories) {
          try {
            const template = await categoriesApi.getTemplateWithStats(category);
            templates[category] = template;
          } catch (error) {
            console.error(`Failed to load template for ${category}:`, error);
            templates[category] = [];
          }
        }
        setCategoryTemplates(templates);
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

  const handleAddAdoptionSkill = (skillName: string) => {
    setAdoptionSelectedSkills(prev => {
      if (!skillName || prev.includes(skillName)) return prev;
      const next = prev.slice(0, Math.max(0, prev.length - 1));
      next.push(skillName);
      return next;
    });
  };

  const AdoptionAxisTick: React.FC<any> = ({ x, y, payload }) => {
    const label: string = payload?.value || '';
    const maxChars = 12;
    const words = label.split(' ');
    const lines: string[] = [];
    let current = '';
    for (const w of words) {
      const test = current ? current + ' ' + w : w;
      if (test.length > maxChars) {
        if (current) lines.push(current);
        current = w;
      } else {
        current = test;
      }
    }
    if (current) lines.push(current);
    const dyStart = 12;
    const dyStep = 12;
    return (
      <g transform={`translate(${x},${y})`}>
        <text textAnchor="middle" fill="#374151" fontSize={12}>
          {lines.slice(0, 3).map((line, i) => (
            <tspan key={i} x={0} dy={i === 0 ? dyStart : dyStep}>{line}</tspan>
          ))}
        </text>
      </g>
    );
  };

  const toggleEmployeeExpanded = (employeeId: string) => {
    setExpandedEmployees(prev => (
      prev.includes(employeeId)
        ? prev.filter(id => id !== employeeId)
        : [...prev, employeeId]
    ));
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

  const handleCategoryImportClick = (category: string) => {
    categoryFileInputRefs.current[category]?.click();
  };

  const handleCategoryFileChange = async (category: string, event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadingCategory(category);
    setUploadError('');
    setSkillsUploadResult(null);

    try {
      const result = await adminApi.importCategoryTemplates(file, category);
      setSkillsUploadResult(result);
      // Reload category templates
      loadDashboardData();
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Failed to upload category template file');
    } finally {
      setUploadingCategory(null);
      // Reset file input
      if (categoryFileInputRefs.current[category]) {
        categoryFileInputRefs.current[category]!.value = '';
      }
    }
  };

  const handleAddCategory = async () => {
    if (!newCategoryName.trim()) return;

    setAddingCategory(true);
    setUploadError('');

    try {
      await categoriesApi.createCategory(newCategoryName.trim());
      setNewCategoryName('');
      setShowAddCategory(false);
      // Reload categories
      loadDashboardData();
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Failed to create category');
    } finally {
      setAddingCategory(false);
    }
  };

  const handleToggleMandatory = async (category: string, templateId: number, currentStatus: boolean) => {
    try {
      const result = await categoriesApi.updateMandatoryStatus(category, templateId, !currentStatus);

      if (result.employees_updated !== undefined && result.employees_updated > 0) {
        setSkillsUploadResult({
          message: result.message,
          rows_processed: result.employees_updated,
          rows_created: result.employees_updated,
          rows_updated: 0,
        });
      }

      // Reload templates
      loadDashboardData();
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Failed to update mandatory status');
    }
  };

  const toggleSubcategory = (key: string) => {
    setExpandedSubcategories(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  // Handler for saving a new skill category
  const handleSaveSkillCategory = async () => {
    if (!newSkillCategoryName.trim()) return;

    setSavingSkillCategory(true);
    setUploadError('');

    try {
      // Create a placeholder skill with the new category to establish the category
      // Use a timestamp to ensure uniqueness
      const timestamp = Date.now();
      await skillsApi.create({
        name: `${newSkillCategoryName.trim()} - Sample Skill ${timestamp}`,
        description: `Sample skill for ${newSkillCategoryName.trim()} category`,
        category: newSkillCategoryName.trim()
      });

      setSkillsUploadResult({
        message: `Skill category "${newSkillCategoryName.trim()}" created successfully`,
        rows_processed: 1,
        rows_created: 1,
        rows_updated: 0,
      });

      setShowAddSkillCategoryModal(false);
      setNewSkillCategoryName('');
      // Reload data to show the new category
      loadDashboardData();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to create skill category';
      setUploadError(errorMessage);
      // Don't close modal on error so user can see the message and try again
    } finally {
      setSavingSkillCategory(false);
    }
  };

  // Handler for saving a new skill
  const handleSaveSkill = async () => {
    if (!newSkillName.trim()) return;

    setSavingSkill(true);
    setUploadError('');

    try {
      console.log('Creating skill:', {
        name: newSkillName.trim(),
        description: `Skill in ${addSkillForCategory} category`,
        category: addSkillForCategory,
        addToCategory: addSkillForPathway
      });

      // Create skill and add it to the employee category template
      await skillsApi.create({
        name: newSkillName.trim(),
        description: `Skill in ${addSkillForCategory} category`,
        category: addSkillForCategory
      }, addSkillForPathway); // Pass the employee category (pathway) to add to template

      setSkillsUploadResult({
        message: `Skill "${newSkillName.trim()}" created successfully in "${addSkillForCategory}"`,
        rows_processed: 1,
        rows_created: 1,
        rows_updated: 0,
      });

      setShowAddSkillModal(false);
      setNewSkillName('');
      // Reload data to show the new skill
      loadDashboardData();
    } catch (err: any) {
      console.error('Error creating skill:', err);
      console.error('Error response:', err.response);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to create skill';
      setUploadError(errorMessage);
      // Don't close modal on error so user can see the message and try again
    } finally {
      setSavingSkill(false);
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
      <PageHeader title="Admin Dashboard" subtitle="Overview of skills, employees, and learning" />

      <div className="max-w-7xl mx-auto px-6 mt-4">
        {/* Tabs */}
        {/* Navigation / Quick Actions */}
        {/* Navigation / Quick Actions */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-gray-800 mb-6 text-center">Quick Actions</h2>
          <div className="flex flex-wrap justify-center gap-4">
            <div
              onClick={() => setActiveTab('overview')}
              className={`bg-white p-4 w-40 h-32 rounded-2xl border-2 ${activeTab === 'overview' ? 'border-red-500 shadow-md ring-2 ring-red-100' : 'border-transparent shadow-sm hover:shadow-md'} cursor-pointer transition-all flex flex-col items-center justify-center text-center gap-2 group`}
            >
              <div className={`p-2 rounded-lg transition-transform ${activeTab === 'overview' ? 'scale-110 bg-red-50' : 'bg-blue-50 group-hover:scale-110'}`}>
                <LayoutGrid className={`w-6 h-6 ${activeTab === 'overview' ? 'text-red-500' : 'text-blue-600'}`} />
              </div>
              <div>
                <h3 className={`font-bold text-sm ${activeTab === 'overview' ? 'text-red-500' : 'text-gray-800'}`}>Overview</h3>
                <p className="text-xs text-gray-500">Summary metrics</p>
              </div>
            </div>

            <div
              onClick={() => { setActiveTab('skill-gap'); navigate('/admin/dashboard?tab=skill-gap'); }}
              className={`bg-white p-4 w-40 h-32 rounded-2xl border-2 ${activeTab === 'skill-gap' ? 'border-red-500 shadow-md ring-2 ring-red-100' : 'border-transparent shadow-sm hover:shadow-md'} cursor-pointer transition-all flex flex-col items-center justify-center text-center gap-2 group`}
            >
              <div className={`p-2 rounded-lg transition-transform ${activeTab === 'skill-gap' ? 'scale-110 bg-red-50' : 'bg-red-50 group-hover:scale-110'}`}>
                <Target className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h3 className={`font-bold text-sm ${activeTab === 'skill-gap' ? 'text-red-500' : 'text-gray-800'}`}>Skill Gap Analysis</h3>
                <p className="text-xs text-gray-500">Analyze gaps</p>
              </div>
            </div>

            <div
              onClick={() => { setActiveTab('employees'); navigate('/admin/dashboard?tab=employees'); }}
              className={`bg-white p-4 w-40 h-32 rounded-2xl border-2 ${activeTab === 'employees' ? 'border-red-500 shadow-md ring-2 ring-red-100' : 'border-transparent shadow-sm hover:shadow-md'} cursor-pointer transition-all flex flex-col items-center justify-center text-center gap-2 group`}
            >
              <div className={`p-2 rounded-lg transition-transform ${activeTab === 'employees' ? 'scale-110 bg-red-50' : 'bg-green-50 group-hover:scale-110'}`}>
                <Users className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <h3 className={`font-bold text-sm ${activeTab === 'employees' ? 'text-red-500' : 'text-gray-800'}`}>Employees</h3>
                <p className="text-xs text-gray-500">Manage employees</p>
              </div>
            </div>

            <div
              onClick={() => { setActiveTab('skills'); navigate('/admin/dashboard?tab=skills'); }}
              className={`bg-white p-4 w-40 h-32 rounded-2xl border-2 ${activeTab === 'skills' ? 'border-red-500 shadow-md ring-2 ring-red-100' : 'border-transparent shadow-sm hover:shadow-md'} cursor-pointer transition-all flex flex-col items-center justify-center text-center gap-2 group`}
            >
              <div className={`p-2 rounded-lg transition-transform ${activeTab === 'skills' ? 'scale-110 bg-red-50' : 'bg-purple-50 group-hover:scale-110'}`}>
                <Award className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h3 className={`font-bold text-sm ${activeTab === 'skills' ? 'text-red-500' : 'text-gray-800'}`}>Skills</h3>
                <p className="text-xs text-gray-500">Browse skills</p>
              </div>
            </div>

            <div
              onClick={() => { setActiveTab('improvements'); navigate('/admin/dashboard?tab=improvements'); }}
              className={`bg-white p-4 w-40 h-32 rounded-2xl border-2 ${activeTab === 'improvements' ? 'border-red-500 shadow-md ring-2 ring-red-100' : 'border-transparent shadow-sm hover:shadow-md'} cursor-pointer transition-all flex flex-col items-center justify-center text-center gap-2 group`}
            >
              <div className={`p-2 rounded-lg transition-transform ${activeTab === 'improvements' ? 'scale-110 bg-red-50' : 'bg-indigo-50 group-hover:scale-110'}`}>
                <TrendingUp className="w-6 h-6 text-indigo-600" />
              </div>
              <div>
                <h3 className={`font-bold text-sm ${activeTab === 'improvements' ? 'text-red-500' : 'text-gray-800'}`}>Improvements</h3>
                <p className="text-xs text-gray-500">Track improvements</p>
              </div>
            </div>

            <div
              onClick={() => { setActiveTab('courses'); navigate('/admin/dashboard?tab=courses'); }}
              className={`bg-white p-4 w-40 h-32 rounded-2xl border-2 ${activeTab === 'courses' ? 'border-red-500 shadow-md ring-2 ring-red-100' : 'border-transparent shadow-sm hover:shadow-md'} cursor-pointer transition-all flex flex-col items-center justify-center text-center gap-2 group`}
            >
              <div className={`p-2 rounded-lg transition-transform ${activeTab === 'courses' ? 'scale-110 bg-red-50' : 'bg-violet-50 group-hover:scale-110'}`}>
                <BookOpen className="w-6 h-6 text-violet-600" />
              </div>
              <div>
                <h3 className={`font-bold text-sm ${activeTab === 'courses' ? 'text-red-500' : 'text-gray-800'}`}>Learning</h3>
                <p className="text-xs text-gray-500">Manage courses</p>
              </div>
            </div>

            <div
              onClick={() => { setActiveTab('career-pathways'); navigate('/admin/dashboard?tab=career-pathways'); }}
              className={`bg-white p-4 w-40 h-32 rounded-2xl border-2 ${activeTab === 'career-pathways' ? 'border-red-500 shadow-md ring-2 ring-red-100' : 'border-transparent shadow-sm hover:shadow-md'} cursor-pointer transition-all flex flex-col items-center justify-center text-center gap-2 group`}
            >
              <div className={`p-2 rounded-lg transition-transform ${activeTab === 'career-pathways' ? 'scale-110 bg-red-50' : 'bg-teal-50 group-hover:scale-110'}`}>
                <Layers className={`w-6 h-6 ${activeTab === 'career-pathways' ? 'text-red-600' : 'text-teal-600'}`} />
              </div>
              <div>
                <h3 className={`font-bold text-sm ${activeTab === 'career-pathways' ? 'text-red-500' : 'text-gray-800'}`}>Career Pathways</h3>
                <p className="text-xs text-gray-500">Skill requirements</p>
              </div>
            </div>
          </div>
        </div>
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
              <h3 className="text-sm font-medium text-gray-500">Total Skill Mappings</h3>
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

        {activeTab === 'overview' && stats && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            {(() => {
              const ratingOrder = ['Beginner', 'Developing', 'Intermediate', 'Advanced', 'Expert'];
              const ratingColors: Record<string, string> = {
                Beginner: '#22c55e',
                Developing: '#3b82f6',
                Intermediate: '#eab308',
                Advanced: '#fb923c',
                Expert: '#a78bfa',
              };
              const ratingData = ratingOrder.map(r => ({ rating: r, count: stats.rating_breakdown[r] || 0, color: ratingColors[r] }));
              const existing = stats.employees_with_existing_skills;
              const existingPie = [
                { name: 'Has Existing Skills', value: existing },
                { name: 'No Existing Skills', value: Math.max(0, stats.total_employees - existing) },
              ];
              const interested = stats.employees_with_interested_skills;
              const interestedPie = [
                { name: 'Has Interested Skills', value: interested },
                { name: 'No Interested Skills', value: Math.max(0, stats.total_employees - interested) },
              ];
              const adoptionData = (adoptionSelectedSkills || []).map(name => {
                const s = (skillsOverview || []).find(x => x.skill.name === name);
                return {
                  name,
                  existing: s ? (s.existing_skills_count || 0) : 0,
                  interested: s ? (s.interested_skills_count || 0) : 0,
                };
              });
              const availableOptions = (skillsOverview || [])
                .map(s => s.skill.name)
                .filter(n => !(adoptionSelectedSkills || []).includes(n));
              const bandRatingsMap: Record<string, { Beginner: number; Developing: number; Intermediate: number; Advanced: number; Expert: number; }> = {};
              (allEmployeesAnalysis || []).forEach(a => {
                const v = Math.round(a.average_rating);
                const t = v <= 1 ? 'Beginner' : v === 2 ? 'Developing' : v === 3 ? 'Intermediate' : v === 4 ? 'Advanced' : 'Expert';
                if (!bandRatingsMap[a.band]) bandRatingsMap[a.band] = { Beginner: 0, Developing: 0, Intermediate: 0, Advanced: 0, Expert: 0 };
                bandRatingsMap[a.band][t] += 1;
              });
              const bandRatingsData = Object.keys(bandRatingsMap).sort().map(b => ({ band: b, ...bandRatingsMap[b] }));
              return (
                <>


                  <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
                    <h3 className="text-sm font-semibold text-gray-800 mb-3">Ratings Trend</h3>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={ratingData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="rating" />
                          <YAxis allowDecimals={false} />
                          <Tooltip />
                          <Legend />
                          <Line type="monotone" dataKey="count" name="Count" stroke="#2563eb" strokeWidth={2} dot={{ r: 3 }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                  <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
                    <h3 className="text-sm font-semibold text-gray-800 mb-3">Employees by Band</h3>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={bandRatingsData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="band" />
                          <YAxis allowDecimals={false} />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="Beginner" stackId="a" fill={ratingColors.Beginner} name="Beginner" />
                          <Bar dataKey="Developing" stackId="a" fill={ratingColors.Developing} name="Developing" />
                          <Bar dataKey="Intermediate" stackId="a" fill={ratingColors.Intermediate} name="Intermediate" />
                          <Bar dataKey="Advanced" stackId="a" fill={ratingColors.Advanced} name="Advanced" />
                          <Bar dataKey="Expert" stackId="a" fill={ratingColors.Expert} name="Expert" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
                    <h3 className="text-sm font-semibold text-gray-800 mb-3">Skill Adoption Overview</h3>
                    <div className="h-64 flex items-center justify-center">
                      <div className="grid grid-cols-2 gap-8 w-full">
                        <div className="text-center">
                          <div className="text-3xl font-bold text-green-600">{existing}</div>
                          <div className="text-sm text-gray-600">Employees with Skills</div>
                          <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-green-500 rounded-full"
                              style={{ width: `${stats.total_employees > 0 ? (existing / stats.total_employees) * 100 : 0}%` }}
                            />
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {stats.total_employees > 0 ? Math.round((existing / stats.total_employees) * 100) : 0}% of total
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="text-3xl font-bold text-indigo-600">{interested}</div>
                          <div className="text-sm text-gray-600">With Interested Skills</div>
                          <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-indigo-500 rounded-full"
                              style={{ width: `${stats.total_employees > 0 ? (interested / stats.total_employees) * 100 : 0}%` }}
                            />
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {stats.total_employees > 0 ? Math.round((interested / stats.total_employees) * 100) : 0}% of total
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="lg:col-span-3">
                    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-sm font-semibold text-gray-800">Top 10 Skills by Adoption</h3>
                        <div className="flex items-center gap-2">
                          <label className="text-xs text-gray-600">Add skill</label>
                          <div className="w-48">
                            <SearchableSelect
                              options={availableOptions.map(n => ({ value: n, label: n }))}
                              value={null}
                              onChange={(v) => handleAddAdoptionSkill(v as string)}
                              placeholder="Add skill..."
                            />
                          </div>
                        </div>
                      </div>
                      <div className="h-96">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={adoptionData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="name" interval={0} tick={<AdoptionAxisTick />} height={60} tickMargin={8} />
                            <YAxis allowDecimals={false} />
                            <Tooltip />
                            <Legend />
                            <Bar dataKey="existing" name="Existing" fill="#10b981" />
                            <Bar dataKey="interested" name="Interested" fill="#6366f1" />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>
                </>
              );
            })()}
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
                    {[5, 10, 20, 50, 100].map(n => <option key={n} value={n}>{n}</option>)}
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
                      .slice((employeesPage - 1) * employeesPerPage, (employeesPage - 1) * employeesPerPage + employeesPerPage)
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
                    {[5, 10, 20, 50, 100].map(n => <option key={n} value={n}>{n}</option>)}
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
                      .slice((employeesPage - 1) * employeesPerPage, (employeesPage - 1) * employeesPerPage + employeesPerPage)
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
            {/* Add Category and Search Section */}
            <div className="mb-6 flex gap-4 items-center">
              <div className="flex-1">
                <input
                  type="text"
                  placeholder="Search categories..."
                  value={categorySearchQuery}
                  onChange={(e) => setCategorySearchQuery(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <button
                onClick={() => {
                  setUploadError('');
                  setShowAddCategory(true);
                }}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium whitespace-nowrap"
              >
                + Add Category
              </button>
            </div>

            {/* Add Category Modal */}
            {showAddCategory && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
                  {/* Header */}
                  <div className="bg-gradient-to-r from-green-600 to-green-700 px-6 py-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h2 className="text-xl font-semibold text-white">Create New Category</h2>
                        <p className="text-green-100 text-sm mt-1">Add a new employee category</p>
                      </div>
                      <button
                        onClick={() => {
                          setShowAddCategory(false);
                          setNewCategoryName('');
                        }}
                        className="text-white/80 hover:text-white transition-colors"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>

                  {/* Body */}
                  <div className="p-6">
                    {uploadError && (
                      <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-sm text-red-800">{uploadError}</p>
                      </div>
                    )}
                    <label className="block text-sm font-medium text-gray-700 mb-2">Category Name</label>
                    <input
                      type="text"
                      placeholder="Enter category name (e.g., Technical, P&C, Consultancy)"
                      value={newCategoryName}
                      onChange={(e) => setNewCategoryName(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleAddCategory()}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all"
                      autoFocus
                      disabled={addingCategory}
                    />
                    <p className="text-xs text-gray-500 mt-2">
                      This will create a new category for organizing employees and their skill templates.
                    </p>
                  </div>

                  {/* Footer */}
                  <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-3">
                    <button
                      onClick={() => {
                        setShowAddCategory(false);
                        setNewCategoryName('');
                      }}
                      disabled={addingCategory}
                      className="px-5 py-2.5 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium transition-colors disabled:opacity-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleAddCategory}
                      disabled={addingCategory || !newCategoryName.trim()}
                      className="px-5 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      {addingCategory ? (
                        <>
                          <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Creating...
                        </>
                      ) : (
                        <>
                          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                          </svg>
                          Save
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {loading ? (
              <div className="text-center py-8 text-gray-500">Loading category templates...</div>
            ) : (
              <div className="space-y-6">
                {employeeCategories.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    No categories found. Click "Add Category" to create one.
                  </div>
                ) : (
                  employeeCategories
                    .filter((category) => {
                      if (categorySearchQuery) {
                        return category.toLowerCase().includes(categorySearchQuery.toLowerCase());
                      }
                      return true;
                    })
                    .sort()
                    .map((category) => {
                      const templates = categoryTemplates[category] || [];
                      const isUploading = uploadingCategory === category;

                      // Group skills by skill category
                      const groupedSkills: Record<string, any[]> = {};
                      templates.forEach((template) => {
                        const skillCategory = template.skill?.category || 'Uncategorized';
                        if (!groupedSkills[skillCategory]) {
                          groupedSkills[skillCategory] = [];
                        }
                        groupedSkills[skillCategory].push(template);
                      });

                      return (
                        <div key={category} className="bg-white rounded-lg shadow-md overflow-hidden">
                          {/* Category Header */}
                          <div className="bg-gray-100 px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                            <div className="flex items-center gap-3">
                              <h2 className="text-xl font-bold text-gray-800">{category}</h2>
                              <span className="text-sm text-gray-600">
                                {templates.length} skill{templates.length !== 1 ? 's' : ''}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => {
                                  setAddSkillCategoryForPathway(category);
                                  setNewSkillCategoryName('');
                                  setUploadError('');
                                  setShowAddSkillCategoryModal(true);
                                }}
                                className="px-3 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 text-sm font-medium"
                                title="Add Skill Category"
                              >
                                + Add Category
                              </button>
                              <button
                                onClick={() => handleCategoryImportClick(category)}
                                disabled={isUploading}
                                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                              >
                                {isUploading ? 'Uploading...' : 'Import Skills'}
                              </button>
                            </div>
                            <input
                              ref={(el) => { categoryFileInputRefs.current[category] = el; }}
                              type="file"
                              accept=".xlsx,.xls"
                              onChange={(e) => handleCategoryFileChange(category, e)}
                              className="hidden"
                            />
                          </div>

                          {/* Skills Table */}
                          {templates.length === 0 ? (
                            <div className="text-center py-12 text-gray-500 bg-gray-50">
                              No skills in this category template. Click "Import Skills" to add skills.
                            </div>
                          ) : (
                            <div>
                              {Object.entries(groupedSkills).sort(([a], [b]) => a.localeCompare(b)).map(([skillCategory, skillTemplates]) => {
                                const subcategoryKey = `${category}-${skillCategory}`;
                                const isExpanded = expandedSubcategories[subcategoryKey] === true; // Default to collapsed

                                return (
                                  <div key={skillCategory} className="border-b border-gray-200 last:border-b-0">
                                    {/* Skill Category Header - Clickable */}
                                    <div
                                      className="bg-gray-50 px-6 py-3 cursor-pointer hover:bg-gray-100 transition-colors flex items-center justify-between"
                                      onClick={() => toggleSubcategory(subcategoryKey)}
                                    >
                                      <h3 className="text-base font-bold text-gray-800">{skillCategory}</h3>
                                      <div className="flex items-center gap-2">
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            console.log('Add Skill clicked', { category, skillCategory });
                                            setAddSkillForPathway(category);
                                            setAddSkillForCategory(skillCategory);
                                            setNewSkillName('');
                                            setUploadError('');
                                            setShowAddSkillModal(true);
                                            console.log('Modal state set to true');
                                          }}
                                          className="px-2 py-1 bg-green-500 text-white rounded hover:bg-green-600 text-xs font-medium"
                                          title="Add Skill to Category"
                                        >
                                          + Add Skill
                                        </button>
                                        <span className="text-sm text-gray-600">
                                          {skillTemplates.length} skill{skillTemplates.length !== 1 ? 's' : ''}
                                        </span>
                                        <svg
                                          className={`w-5 h-5 text-gray-600 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                                          fill="none"
                                          stroke="currentColor"
                                          viewBox="0 0 24 24"
                                        >
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                        </svg>
                                      </div>
                                    </div>

                                    {/* Table - Collapsible */}
                                    {isExpanded && (
                                      <div className="overflow-x-auto">
                                        <table className="min-w-full divide-y divide-gray-200">
                                          <thead className="bg-gray-50">
                                            <tr>
                                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                Skill
                                              </th>
                                              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-32">
                                                Mandatory
                                              </th>
                                              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                                                Employees
                                              </th>
                                              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                                                Beginner
                                              </th>
                                              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                                                Developing
                                              </th>
                                              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                                                Intermediate
                                              </th>
                                              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                                                Advanced
                                              </th>
                                              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                                                Expert
                                              </th>
                                            </tr>
                                          </thead>
                                          <tbody className="bg-white divide-y divide-gray-200">
                                            {skillTemplates.map((template) => (
                                              <tr key={template.id} className="hover:bg-gray-50">
                                                <td className="px-6 py-4">
                                                  <div className="text-sm font-medium text-gray-900">
                                                    {template.skill?.name || 'Unknown Skill'}
                                                  </div>
                                                  {template.skill?.description && (
                                                    <div className="text-xs text-gray-500 mt-1">
                                                      {template.skill.description}
                                                    </div>
                                                  )}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-center">
                                                  {template.is_required ? (
                                                    <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded">
                                                      Mandatory Skill
                                                    </span>
                                                  ) : (
                                                    <input
                                                      type="checkbox"
                                                      id={`mandatory-${template.id}`}
                                                      checked={false}
                                                      onChange={() => handleToggleMandatory(category, template.id, template.is_required)}
                                                      className="w-4 h-4 text-red-600 bg-gray-100 border-gray-300 rounded focus:ring-red-500 cursor-pointer"
                                                      title="Mark as Mandatory"
                                                    />
                                                  )}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-semibold text-gray-900">
                                                  {template.total_employees}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                                                  {template.rating_breakdown?.Beginner || 0}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                                                  {template.rating_breakdown?.Developing || 0}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                                                  {template.rating_breakdown?.Intermediate || 0}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                                                  {template.rating_breakdown?.Advanced || 0}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                                                  {template.rating_breakdown?.Expert || 0}
                                                </td>
                                              </tr>
                                            ))}
                                          </tbody>
                                        </table>
                                      </div>
                                    )}
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      );
                    })
                )}
                {employeeCategories.filter((category) => {
                  if (categorySearchQuery) {
                    return category.toLowerCase().includes(categorySearchQuery.toLowerCase());
                  }
                  return true;
                }).length === 0 && categorySearchQuery && (
                    <div className="text-center py-8 text-gray-500">
                      No categories found matching "{categorySearchQuery}"
                    </div>
                  )}
              </div>
            )}

            {/* Template Management Section */}
            <TemplateManagement
              onUploadSuccess={(result) => {
                // Convert TemplateUploadResponse to UploadResponse format
                setSkillsUploadResult({
                  message: result.message,
                  rows_processed: result.templates_created,
                  rows_created: result.templates_created,
                  rows_updated: 0,
                });
              }}
              onUploadError={(error) => setUploadError(error)}
            />
          </div>
        )}

        {/* Career Pathways Tab */}
        {activeTab === 'career-pathways' && (
          <div className="mt-6">
            <CareerPathways isEmbedded={true} />
          </div>
        )}

        {/* Skill Gap Analysis Tab */}
        {activeTab === 'skill-gap' && (
          <div>
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-2">Skill Gap Analysis</h2>
              <p className="text-sm text-gray-600">View employees with and without skill gaps based on their band requirements</p>
            </div>

            {loadingSkillGap ? (
              <div className="text-center py-8 text-gray-500">Loading skill gap analysis...</div>
            ) : (() => {
              // Separate employees into two groups: with gaps and without gaps
              const employeesWithGaps = allEmployeesAnalysis.filter(analysis =>
                analysis.skills_below_requirement > 0
              );
              const employeesWithoutGaps = allEmployeesAnalysis.filter(analysis =>
                analysis.skills_below_requirement === 0
              );

              return (
                <>
                  {/* Section 1: Employees WITH Gaps */}
                  <div className="mb-8">
                    <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-lg font-bold text-red-800">Employees WITH Skill Gaps</h3>
                          <p className="text-sm text-red-700 mt-1">
                            {employeesWithGaps.length} employee(s) have skills below requirements
                          </p>
                        </div>
                        <div className="text-3xl font-bold text-red-600">{employeesWithGaps.length}</div>
                      </div>
                    </div>

                    {employeesWithGaps.length === 0 ? (
                      <div className="bg-white rounded-lg shadow-sm p-8 text-center">
                        <svg className="w-16 h-16 mx-auto mb-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <p className="text-lg font-medium text-gray-900">No employees with skill gaps!</p>
                        <p className="text-sm text-gray-500 mt-1">All employees meet their band requirements.</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {employeesWithGaps.map((analysis) => (
                          <div
                            key={analysis.employee_id}
                            className="bg-white rounded-lg shadow-md border-l-4 border-red-500 overflow-hidden cursor-pointer hover:shadow-lg transition-shadow"
                            onClick={() => toggleEmployeeExpanded(analysis.employee_id)}
                          >
                            <div className="bg-gradient-to-r from-red-50 to-orange-50 px-6 py-4">
                              <div className="flex justify-between items-center">
                                <div>
                                  <h3 className="text-lg font-semibold text-gray-900">{analysis.employee_name}</h3>
                                  <p className="text-sm text-gray-600">Employee ID: {analysis.employee_id}</p>
                                </div>
                                <div className="flex items-center gap-4">
                                  <div className="text-center">
                                    <div className="text-xs text-gray-500 mb-1">Band</div>
                                    <div className="text-2xl font-bold text-indigo-600">{analysis.band}</div>
                                  </div>
                                  <div className="text-center">
                                    <div className="text-xs text-gray-500 mb-1">Gaps</div>
                                    <div className="text-2xl font-bold text-red-600">{analysis.skills_below_requirement}</div>
                                  </div>
                                  <div className="text-center">
                                    <div className="text-xs text-gray-500 mb-1">Total Skills</div>
                                    <div className="text-lg font-semibold text-gray-900">{analysis.total_skills}</div>
                                  </div>
                                  <span className="flex items-center p-2 text-gray-700">
                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={`w-4 h-4 transition-transform ${expandedEmployees.includes(analysis.employee_id) ? 'rotate-180' : ''}`}>
                                      <polyline points="6 9 12 15 18 9"></polyline>
                                    </svg>
                                  </span>
                                </div>
                              </div>
                              <div className="mt-4 flex gap-4">
                                <div className="flex items-center gap-2">
                                  <span className="inline-block w-3 h-3 rounded-full bg-green-500"></span>
                                  <span className="text-sm text-gray-700">Above: {analysis.skills_above_requirement}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <span className="inline-block w-3 h-3 rounded-full bg-gray-400"></span>
                                  <span className="text-sm text-gray-700">At: {analysis.skills_at_requirement}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <span className="inline-block w-3 h-3 rounded-full bg-red-500"></span>
                                  <span className="text-sm text-gray-700">Below: {analysis.skills_below_requirement}</span>
                                </div>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedEmployeeForSkills({
                                      employee_id: analysis.employee_id,
                                      employee_name: analysis.employee_name,
                                      band: analysis.band,
                                      skills: analysis.skill_gaps
                                    });
                                    setShowSkillsModal(true);
                                  }}
                                  className="ml-auto text-blue-600 hover:text-blue-800 transition-colors flex items-center gap-1"
                                  title="View all skills"
                                >
                                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                  </svg>
                                  <span className="text-sm font-medium">View Skills</span>
                                </button>
                              </div>
                            </div>
                            {expandedEmployees.includes(analysis.employee_id) && (
                              analysis.skill_gaps.length > 0 ? (
                                <div className="overflow-x-auto">
                                  <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-gray-50">
                                      <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Skill</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Source</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Current Rating</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Required Rating</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Gap</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Status</th>
                                      </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-200">
                                      {analysis.skill_gaps.filter(gap => gap.gap < 0).map((gap, idx) => {
                                        const getGapColor = (gap: number) => {
                                          if (gap > 0) return 'bg-green-100 text-green-800';
                                          if (gap === 0) return 'bg-gray-100 text-gray-800';
                                          return 'bg-red-100 text-red-800';
                                        };
                                        const getRatingColor = (rating?: string) => {
                                          switch (rating) {
                                            case 'Expert': return 'bg-purple-100 text-purple-800';
                                            case 'Advanced': return 'bg-orange-100 text-orange-800';
                                            case 'Intermediate': return 'bg-yellow-100 text-yellow-800';
                                            case 'Developing': return 'bg-blue-100 text-blue-800';
                                            case 'Beginner': return 'bg-green-100 text-green-800';
                                            case 'Not Rated': return 'bg-red-50 text-red-600 border border-red-200';
                                            default: return 'bg-gray-100 text-gray-600';
                                          }
                                        };
                                        const getSourceBadge = (source: string) => {
                                          switch (source) {
                                            case 'Template': return 'bg-blue-100 text-blue-800';
                                            case 'Role': return 'bg-purple-100 text-purple-800';
                                            case 'Band Default': return 'bg-gray-100 text-gray-600';
                                            default: return 'bg-gray-100 text-gray-800';
                                          }
                                        }

                                        return (
                                          <tr key={idx} className="hover:bg-gray-50">
                                            <td className="px-6 py-4 whitespace-nowrap">
                                              <div className="text-sm font-medium text-gray-900">{gap.skill_name}</div>
                                              <div className="text-xs text-gray-500 mt-0.5">{gap.skill_category || 'N/A'}</div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getSourceBadge(gap.requirement_source)}`}>
                                                {gap.requirement_source}
                                              </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                              {gap.current_rating_text ? (
                                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRatingColor(gap.current_rating_text)}`}>
                                                  {gap.current_rating_text} {gap.current_rating_number ? `(${gap.current_rating_number})` : ''}
                                                </span>
                                              ) : (
                                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                                  Missing
                                                </span>
                                              )}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRatingColor(gap.required_rating_text)}`}>
                                                {gap.required_rating_text} ({gap.required_rating_number})
                                              </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getGapColor(gap.gap)}`}>
                                                {gap.gap > 0 ? '+' : ''}{gap.gap}
                                              </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 w-fit">
                                                Below
                                              </span>
                                            </td>
                                          </tr>
                                        );
                                      })}
                                    </tbody>
                                  </table>
                                </div>
                              ) : (
                                <div className="px-6 py-8 text-center text-sm text-gray-500">
                                  No skill gaps found for this employee.
                                </div>
                              )
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Section 2: Employees WITHOUT Gaps */}
                  <div>
                    <div className="bg-green-50 border-l-4 border-green-500 p-4 mb-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-lg font-bold text-green-800">Employees WITHOUT Skill Gaps</h3>
                          <p className="text-sm text-green-700 mt-1">
                            {employeesWithoutGaps.length} employee(s) meet all requirements
                          </p>
                        </div>
                        <div className="text-3xl font-bold text-green-600">{employeesWithoutGaps.length}</div>
                      </div>
                    </div>

                    {employeesWithoutGaps.length === 0 ? (
                      <div className="bg-white rounded-lg shadow-sm p-8 text-center">
                        <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                        </svg>
                        <p className="text-lg font-medium text-gray-900">No employees without gaps yet</p>
                        <p className="text-sm text-gray-500 mt-1">Employees who meet all requirements will appear here.</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {employeesWithoutGaps.map((analysis) => (
                          <div
                            key={analysis.employee_id}
                            className="bg-white rounded-lg shadow-md border-l-4 border-green-500 overflow-hidden"
                          >
                            <div className="bg-gradient-to-r from-green-50 to-emerald-50 px-6 py-4">
                              <div className="flex justify-between items-center">
                                <div>
                                  <h3 className="text-lg font-semibold text-gray-900">{analysis.employee_name}</h3>
                                  <p className="text-sm text-gray-600">Employee ID: {analysis.employee_id}</p>
                                </div>
                                <div className="flex items-center gap-4">
                                  <div className="text-center">
                                    <div className="text-xs text-gray-500 mb-1">Band</div>
                                    <div className="text-2xl font-bold text-indigo-600">{analysis.band}</div>
                                  </div>
                                  <div className="text-center">
                                    <div className="text-xs text-gray-500 mb-1">Avg Rating</div>
                                    <div className="text-lg font-semibold text-gray-900">{analysis.average_rating.toFixed(2)}</div>
                                  </div>
                                  <div className="text-center">
                                    <div className="text-xs text-gray-500 mb-1">Total Skills</div>
                                    <div className="text-lg font-semibold text-gray-900">{analysis.total_skills}</div>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                  </div>
                                </div>
                              </div>
                              <div className="mt-4 flex gap-4">
                                <div className="flex items-center gap-2">
                                  <span className="inline-block w-3 h-3 rounded-full bg-green-500"></span>
                                  <span className="text-sm text-gray-700">Above: {analysis.skills_above_requirement}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <span className="inline-block w-3 h-3 rounded-full bg-gray-400"></span>
                                  <span className="text-sm text-gray-700">At: {analysis.skills_at_requirement}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <span className="inline-block w-3 h-3 rounded-full bg-gray-300"></span>
                                  <span className="text-sm text-gray-700">Below: 0</span>
                                </div>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedEmployeeForSkills({
                                      employee_id: analysis.employee_id,
                                      employee_name: analysis.employee_name,
                                      band: analysis.band,
                                      skills: analysis.skill_gaps
                                    });
                                    setShowSkillsModal(true);
                                  }}
                                  className="ml-auto text-blue-600 hover:text-blue-800 transition-colors flex items-center gap-1"
                                  title="View all skills"
                                >
                                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                  </svg>
                                  <span className="text-sm font-medium">View Skills</span>
                                </button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </>
              );
            })()}

            {/* Skills Modal */}
            {showSkillsModal && selectedEmployeeForSkills && (
              <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
                <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
                  <div
                    className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
                    aria-hidden="true"
                    onClick={() => setShowSkillsModal(false)}
                  ></div>

                  <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
                  <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-5xl sm:w-full">
                    {/* Header */}
                    <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-lg font-semibold text-white" id="modal-title">
                            {selectedEmployeeForSkills.employee_name}'s Skills
                          </h3>
                          <p className="text-sm text-blue-100 mt-1">
                            Band {selectedEmployeeForSkills.band} • {selectedEmployeeForSkills.skills.length} skills
                          </p>
                        </div>
                        <button
                          onClick={() => setShowSkillsModal(false)}
                          className="text-white hover:text-gray-200 transition-colors"
                        >
                          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    </div>

                    {/* Content */}
                    <div className="bg-white px-6 py-4 max-h-[70vh] overflow-y-auto">
                      {selectedEmployeeForSkills.skills.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">No skills found</div>
                      ) : (
                        <div className="overflow-x-auto">
                          <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                              <tr>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Skill Name</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Source</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Rating</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Required Rating</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Gap</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                              </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                              {selectedEmployeeForSkills.skills.map((skill, index) => {
                                const getGapColor = (gap: number) => {
                                  if (gap > 0) return 'bg-green-100 text-green-800';
                                  if (gap === 0) return 'bg-gray-100 text-gray-800';
                                  return 'bg-red-100 text-red-800';
                                };
                                const getRatingColor = (rating?: string) => {
                                  switch (rating) {
                                    case 'Expert': return 'bg-purple-100 text-purple-800';
                                    case 'Advanced': return 'bg-orange-100 text-orange-800';
                                    case 'Intermediate': return 'bg-yellow-100 text-yellow-800';
                                    case 'Developing': return 'bg-blue-100 text-blue-800';
                                    case 'Beginner': return 'bg-green-100 text-green-800';
                                    case 'Not Rated': return 'bg-red-50 text-red-600 border border-red-200';
                                    default: return 'bg-gray-100 text-gray-600';
                                  }
                                };
                                const getSourceBadge = (source: string) => {
                                  switch (source) {
                                    case 'Template': return 'bg-blue-100 text-blue-800';
                                    case 'Role': return 'bg-purple-100 text-purple-800';
                                    case 'Band Default': return 'bg-gray-100 text-gray-600';
                                    default: return 'bg-gray-100 text-gray-800';
                                  }
                                };

                                return (
                                  <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                                      {skill.skill_name}
                                    </td>
                                    <td className="px-4 py-3 text-sm text-gray-600">
                                      {skill.skill_category || '-'}
                                    </td>
                                    <td className="px-4 py-3 text-sm">
                                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getSourceBadge(skill.requirement_source)}`}>
                                        {skill.requirement_source}
                                      </span>
                                    </td>
                                    <td className="px-4 py-3 text-sm">
                                      {skill.current_rating_text ? (
                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRatingColor(skill.current_rating_text)}`}>
                                          {skill.current_rating_text} {skill.current_rating_number ? `(${skill.current_rating_number})` : ''}
                                        </span>
                                      ) : (
                                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                          Not Rated
                                        </span>
                                      )}
                                    </td>
                                    <td className="px-4 py-3 text-sm">
                                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRatingColor(skill.required_rating_text)}`}>
                                        {skill.required_rating_text} ({skill.required_rating_number})
                                      </span>
                                    </td>
                                    <td className="px-4 py-3 text-sm">
                                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getGapColor(skill.gap)}`}>
                                        {skill.gap > 0 ? '+' : ''}{skill.gap}
                                      </span>
                                    </td>
                                    <td className="px-4 py-3 text-sm">
                                      {skill.gap < 0 ? (
                                        <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                                          Below
                                        </span>
                                      ) : skill.gap === 0 ? (
                                        <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                                          Met
                                        </span>
                                      ) : (
                                        <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                                          Exceeded
                                        </span>
                                      )}
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>

                    {/* Footer */}
                    <div className="bg-gray-50 px-6 py-3 flex justify-end">
                      <button
                        onClick={() => setShowSkillsModal(false)}
                        className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
                      >
                        Close
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'improvements' && (
          <div>
            <div className="flex justify-end items-center mb-2">
              <label className="text-sm text-gray-600 mr-2">Rows per page</label>
              <select
                value={imprPerPage}
                onChange={(e) => { setImprPerPage(Number(e.target.value)); setImprPage(1); }}
                className="px-2 py-1 border border-gray-300 rounded-lg bg-white text-sm"
              >
                {[5, 10, 20, 50, 100].map(n => <option key={n} value={n}>{n}</option>)}
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
                {(() => {
                  const grouped: Array<{ employee_id: string; employee_name: string; items: SkillImprovement[] }> = [];
                  const byId: Record<string, number> = {};
                  improvements.forEach((imp) => {
                    const key = imp.employee_id;
                    if (byId[key] === undefined) {
                      byId[key] = grouped.length;
                      grouped.push({ employee_id: imp.employee_id, employee_name: imp.employee_name, items: [imp] });
                    } else {
                      grouped[byId[key]].items.push(imp);
                    }
                  });

                  if (grouped.length === 0) {
                    return (
                      <table className="min-w-full divide-y divide-gray-200">
                        <tbody>
                          <tr>
                            <td className="px-6 py-8 text-center text-sm text-gray-500">No skill improvements found. Employees need to upgrade their skill ratings to appear here.</td>
                          </tr>
                        </tbody>
                      </table>
                    );
                  }

                  const start = (imprPage - 1) * imprPerPage;
                  const end = start + imprPerPage;
                  const pageItems = grouped.slice(start, end);

                  return (
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Employee</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Improvements</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Show More</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {pageItems.map((grp, idx) => (
                          <>
                            <tr key={`${grp.employee_id}-row`} className="hover:bg-gray-50">
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                {grp.employee_name} ({grp.employee_id})
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {grp.items.length}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                <button
                                  onClick={() => setExpandedImprovementEmployees(prev => prev.includes(grp.employee_id) ? prev.filter(id => id !== grp.employee_id) : [...prev, grp.employee_id])}
                                  className="px-3 py-1 rounded-md border border-gray-300 text-xs bg-white hover:bg-gray-50"
                                >
                                  {expandedImprovementEmployees.includes(grp.employee_id) ? 'Hide' : 'Show More'}
                                </button>
                              </td>
                            </tr>
                            {expandedImprovementEmployees.includes(grp.employee_id) && (
                              <tr key={`${grp.employee_id}-details`}>
                                <td colSpan={3} className="px-6 py-4">
                                  <div className="overflow-x-auto">
                                    <table className="min-w-full divide-y divide-gray-200">
                                      <thead className="bg-gray-50">
                                        <tr>
                                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Skill</th>
                                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Initial Rating</th>
                                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Current Rating</th>
                                        </tr>
                                      </thead>
                                      <tbody className="bg-white divide-y divide-gray-200">
                                        {grp.items.map((impItem, i) => (
                                          <tr key={`${grp.employee_id}-${i}`} className="hover:bg-gray-50">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{impItem.skill_name}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{impItem.initial_rating}</td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">{impItem.current_rating}</span>
                                            </td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                </td>
                              </tr>
                            )}
                          </>
                        ))}
                      </tbody>
                    </table>
                  );
                })()}
                <div className="flex justify-end items-center gap-2 p-3">
                  {(() => {
                    const groupedCount = (() => {
                      const ids: Record<string, boolean> = {};
                      improvements.forEach(i => { ids[i.employee_id] = true; });
                      return Object.keys(ids).length;
                    })();
                    const total = groupedCount;
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

        {/* Courses Management Tab */}
        {activeTab === 'courses' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-800 mb-2">Course Management</h2>
                <p className="text-sm text-gray-600">Create and manage learning courses, link them to skills, and assign them to employees.</p>
              </div>
              <button
                onClick={handleCreateCourse}
                className="flex items-center gap-2 bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
                </svg>
                Create Course
              </button>
            </div>

            {loadingCourses ? (
              <div className="text-center py-12 text-gray-500">Loading courses...</div>
            ) : courses.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg shadow border border-gray-200">
                <svg xmlns="http://www.w3.org/2000/svg" className="mx-auto h-12 w-12 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                <h3 className="text-lg font-medium text-gray-900 mb-1">No courses found</h3>
                <p className="text-gray-500 mb-4">Get started by creating your first course.</p>
                <button
                  onClick={handleCreateCourse}
                  className="text-yellow-600 hover:text-yellow-800 font-medium"
                >
                  Create a new course
                </button>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow overflow-hidden border border-gray-200">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Course Title</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Linked Skill</th>
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Access</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {courses.map((course) => (
                      <tr key={course.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <div className="text-sm font-medium text-gray-900">{course.title}</div>
                          {course.description && <div className="text-sm text-gray-500 mt-1">{course.description}</div>}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {course.skill_name ? (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              {course.skill_name}
                            </span>
                          ) : (
                            <span className="text-sm text-gray-400">No skill linked</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-center">
                          {course.is_mandatory ? (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                              Mandatory
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              Optional
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-center">
                          {course.external_url ? (
                            <a
                              href={course.external_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-blue-600 hover:text-blue-800 hover:underline flex items-center justify-center gap-1"
                            >
                              External Link
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                              </svg>
                            </a>
                          ) : (
                            <span className="text-sm text-gray-500">Internal</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex items-center justify-end gap-3">
                            <button
                              onClick={() => handleOpenAssignModal(course)}
                              className="text-blue-600 hover:text-blue-900 font-medium"
                            >
                              Assign
                            </button>
                            <button
                              onClick={() => handleDeleteCourse(course.id)}
                              className="text-red-600 hover:text-red-900"
                            >
                              Delete
                            </button>
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

        {/* Add Skill Category Modal */}
        {showAddSkillCategoryModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
              {/* Header */}
              <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-white">Add Skill Category</h2>
                    <p className="text-blue-100 text-sm mt-1">Add a new skill category to "{addSkillCategoryForPathway}"</p>
                  </div>
                  <button
                    onClick={() => {
                      setShowAddSkillCategoryModal(false);
                      setNewSkillCategoryName('');
                    }}
                    className="text-white/80 hover:text-white transition-colors"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Body */}
              <div className="p-6">
                {uploadError && (
                  <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm text-red-800">{uploadError}</p>
                  </div>
                )}
                <label className="block text-sm font-medium text-gray-700 mb-2">Category Name</label>
                <input
                  type="text"
                  value={newSkillCategoryName}
                  onChange={(e) => setNewSkillCategoryName(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSaveSkillCategory()}
                  placeholder="e.g., Technical Skills, Soft Skills"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                  autoFocus
                  disabled={savingSkillCategory}
                />
                <p className="text-xs text-gray-500 mt-2">
                  This will create a new skill category that can be used to organize skills.
                </p>
              </div>

              {/* Footer */}
              <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-3">
                <button
                  onClick={() => {
                    setShowAddSkillCategoryModal(false);
                    setNewSkillCategoryName('');
                  }}
                  disabled={savingSkillCategory}
                  className="px-5 py-2.5 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveSkillCategory}
                  disabled={!newSkillCategoryName.trim() || savingSkillCategory}
                  className="px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {savingSkillCategory ? (
                    <>
                      <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Saving...
                    </>
                  ) : (
                    <>
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                      Save
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Add Skill Modal */}
        {(() => {
          console.log('Rendering Add Skill Modal - showAddSkillModal:', showAddSkillModal);
          return showAddSkillModal;
        })() && (
            <div
              className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]"
              onClick={(e) => {
                if (e.target === e.currentTarget) {
                  setShowAddSkillModal(false);
                  setNewSkillName('');
                }
              }}
            >
              <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden" onClick={(e) => e.stopPropagation()}>
                {/* Header */}
                <div className="bg-gradient-to-r from-green-600 to-green-700 px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-xl font-semibold text-white">Add Skill</h2>
                      <p className="text-green-100 text-sm mt-1">Add a new skill to "{addSkillForCategory}"</p>
                    </div>
                    <button
                      onClick={() => {
                        setShowAddSkillModal(false);
                        setNewSkillName('');
                      }}
                      className="text-white/80 hover:text-white transition-colors"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>

                {/* Body */}
                <div className="p-6">
                  {uploadError && (
                    <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm text-red-800">{uploadError}</p>
                    </div>
                  )}
                  <label className="block text-sm font-medium text-gray-700 mb-2">Skill Name</label>
                  <input
                    type="text"
                    value={newSkillName}
                    onChange={(e) => setNewSkillName(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSaveSkill()}
                    placeholder="e.g., Python, Project Management"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all"
                    autoFocus
                    disabled={savingSkill}
                  />
                  <p className="text-xs text-gray-500 mt-2">
                    This skill will be added to the "{addSkillForCategory}" category.
                  </p>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-3">
                  <button
                    onClick={() => {
                      setShowAddSkillModal(false);
                      setNewSkillName('');
                    }}
                    disabled={savingSkill}
                    className="px-5 py-2.5 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium transition-colors disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveSkill}
                    disabled={!newSkillName.trim() || savingSkill}
                    className="px-5 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    {savingSkill ? (
                      <>
                        <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Saving...
                      </>
                    ) : (
                      <>
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                        Save
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}

        {/* Bulk Assignment Modal */}
        {showAssignModal && assignCourse && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl mx-4 overflow-hidden flex flex-col max-h-[85vh]">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-700 px-6 py-4 flex-shrink-0">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-white">Assign Course</h2>
                    <p className="text-blue-100 text-sm mt-1">Assign "{assignCourse.title}" to employees</p>
                  </div>
                  <button
                    onClick={() => setShowAssignModal(false)}
                    className="text-white/80 hover:text-white transition-colors"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              <div className="p-4 border-b border-gray-200 flex-shrink-0 space-y-3">
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Search employees by name or ID..."
                    value={assignmentSearchQuery}
                    onChange={(e) => setAssignmentSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <svg className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>

                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">
                    {selectedEmployeeIds.length} employee{selectedEmployeeIds.length !== 1 ? 's' : ''} selected
                  </span>
                  <button
                    onClick={handleSelectAllFilteredEmployees}
                    type="button"
                    className="text-blue-600 hover:text-blue-800 font-medium"
                  >
                    {(() => {
                      const filtered = employees.filter(e =>
                        e.name.toLowerCase().includes(assignmentSearchQuery.toLowerCase()) ||
                        e.employee_id.toLowerCase().includes(assignmentSearchQuery.toLowerCase())
                      );
                      const allFilteredSelected = filtered.length > 0 && filtered.every(e => selectedEmployeeIds.includes(e.id));
                      return allFilteredSelected ? 'Deselect All' : 'Select All Filtered';
                    })()}
                  </button>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-2">
                {employees.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">Loading employees...</div>
                ) : (
                  <div className="space-y-1">
                    {employees
                      .filter(e =>
                        e.name.toLowerCase().includes(assignmentSearchQuery.toLowerCase()) ||
                        e.employee_id.toLowerCase().includes(assignmentSearchQuery.toLowerCase())
                      )
                      .map(employee => (
                        <div
                          key={employee.id}
                          onClick={() => toggleEmployeeSelection(employee.id)}
                          className={`flex items-center p-3 rounded-lg cursor-pointer border transition-colors ${selectedEmployeeIds.includes(employee.id)
                            ? 'bg-blue-50 border-blue-200'
                            : 'hover:bg-gray-50 border-transparent'
                            }`}
                        >
                          <div className="flex-shrink-0 mr-3">
                            <div className={`w-5 h-5 rounded border flex items-center justify-center ${selectedEmployeeIds.includes(employee.id)
                              ? 'bg-blue-600 border-blue-600'
                              : 'border-gray-300 bg-white'
                              }`}>
                              {selectedEmployeeIds.includes(employee.id) && (
                                <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                </svg>
                              )}
                            </div>
                          </div>
                          <div className="flex-1">
                            <div className="font-medium text-gray-900">{employee.name}</div>
                            <div className="text-xs text-gray-500">
                              {employee.employee_id} • {employee.department || 'No Dept'} • {employee.role || 'No Role'}
                            </div>
                          </div>
                        </div>
                      ))}
                    {employees.filter(e =>
                      e.name.toLowerCase().includes(assignmentSearchQuery.toLowerCase()) ||
                      e.employee_id.toLowerCase().includes(assignmentSearchQuery.toLowerCase())
                    ).length === 0 && (
                        <div className="text-center py-8 text-gray-500">
                          No employees found matching "{assignmentSearchQuery}"
                        </div>
                      )}
                  </div>
                )}
              </div>

              <div className="p-4 border-t border-gray-200 bg-gray-50 flex justify-end gap-3 flex-shrink-0">
                <button
                  onClick={() => setShowAssignModal(false)}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAssignCourse}
                  disabled={selectedEmployeeIds.length === 0 || assigning}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {assigning ? 'Assigning...' : `Assign to ${selectedEmployeeIds.length} Employees`}
                </button>
              </div>
            </div>
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
    </div >
  );
};

