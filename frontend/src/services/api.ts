/** API service for backend communication. */
import axios from 'axios';

// Use relative path to leverage Vite proxy, or fallback to env variable
// In development with Vite proxy, use empty string (relative paths)
// In production or when proxy is not available, use full URL
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors (unauthorized)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Types
export interface Skill {
  id: number;
  name: string;
  description?: string;
  category?: string;
}

export interface Employee {
  id: number;
  employee_id: string;
  name: string;
  first_name?: string;
  last_name?: string;
  company_email?: string;
  department?: string;
  role?: string;
  team?: string;
  band?: string;
  category?: string;
}

export interface EmployeeSkill {
  id: number;
  employee_id: number;
  skill_id: number;
  rating?: 'Beginner' | 'Developing' | 'Intermediate' | 'Advanced' | 'Expert' | null;  // Optional for interested skills
  years_experience?: number;
  is_interested?: boolean;
  notes?: string;
  is_custom?: boolean;
  employee?: {
    id: number;
    employee_id: string;
    name: string;
  };
  skill?: Skill;
}

export interface User {
  id: number;
  email: string;
  employee_id?: string;
  is_active: boolean;
  is_admin: boolean;
  must_change_password: boolean;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
  user: User;
}

export interface FuzzySearchResult {
  employee_id: string;
  employee_name: string;
  overall_match_score: number;
  matched_skills: Array<{
    skill_name: string;
    match_score: number;
  }>;
  ratings: Array<{
    skill_name: string;
    rating: string;
    years_experience?: number;
  }>;
}

export interface UploadResponse {
  message: string;
  rows_processed: number;
  rows_created: number;
  rows_updated: number;
  errors?: string[];
}

// Skills API
export const skillsApi = {
  getAll: async (): Promise<Skill[]> => {
    const response = await api.get<Skill[]>('/api/skills/');
    return response.data;
  },
  getAllSimple: async (limit: number = 1000): Promise<Skill[]> => {
    // Use the simple /all endpoint that doesn't do category filtering
    const response = await api.get<Skill[]>('/api/skills/all', { params: { limit } });
    return response.data;
  },
  getById: async (id: number): Promise<Skill> => {
    const response = await api.get<Skill>(`/api/skills/${id}`);
    return response.data;
  },
  create: async (skill: { name: string; description?: string; category?: string }, addToCategory?: string): Promise<Skill> => {
    const params = addToCategory ? { add_to_category: addToCategory } : {};
    const response = await api.post<Skill>('/api/skills/', skill, { params });
    return response.data;
  },
};

// Auth API
export const authApi = {
  login: async (email: string, password: string): Promise<Token> => {
    const response = await api.post<Token>('/api/auth/login', { email, password });
    // Store token and user
    localStorage.setItem('auth_token', response.data.access_token);
    localStorage.setItem('user', JSON.stringify(response.data.user));
    return response.data;
  },
  register: async (data: {
    email: string;
    password: string;
    employee_id?: string;
    first_name?: string;
    last_name?: string;
  }): Promise<User> => {
    const response = await api.post<User>('/api/auth/register', data);
    return response.data;
  },
  getMe: async (): Promise<User> => {
    const response = await api.get<User>('/api/auth/me');
    return response.data;
  },
  changePassword: async (currentPassword: string, newPassword: string): Promise<User> => {
    const response = await api.post<User>('/api/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response.data;
  },
  logout: () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
  },
  getToken: (): string | null => {
    return localStorage.getItem('auth_token');
  },
  getUser: (): User | null => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },
};

// User Skills API
export const userSkillsApi = {
  getMyEmployee: async (): Promise<Employee> => {
    const response = await api.get<Employee>('/api/user-skills/me/employee');
    return response.data;
  },
  getMySkills: async (): Promise<EmployeeSkill[]> => {
    const response = await api.get<EmployeeSkill[]>('/api/user-skills/me');
    return response.data;
  },
  getByEmployeeId: async (employeeId: string): Promise<EmployeeSkill[]> => {
    const response = await api.get<EmployeeSkill[]>(`/api/user-skills/employee/${employeeId}`);
    return response.data;
  },
  createMySkill: async (data: {
    skill_name: string;
    skill_category?: string;  // Optional category for the skill
    rating?: 'Beginner' | 'Developing' | 'Intermediate' | 'Advanced' | 'Expert';  // Optional for interested skills
    years_experience?: number;
    is_interested?: boolean;
    notes?: string;
    is_custom?: boolean;
  }): Promise<EmployeeSkill> => {
    const response = await api.post<EmployeeSkill>('/api/user-skills/me', data);
    return response.data;
  },
  create: async (data: {
    employee_id: string;
    skill_name: string;
    rating: 'Beginner' | 'Developing' | 'Intermediate' | 'Advanced' | 'Expert';
    years_experience?: number;
    is_interested?: boolean;
    notes?: string;
  }): Promise<EmployeeSkill> => {
    const response = await api.post<EmployeeSkill>('/api/user-skills/', data);
    return response.data;
  },
  updateMySkill: async (id: number, data: {
    rating?: 'Beginner' | 'Developing' | 'Intermediate' | 'Advanced' | 'Expert';
    years_experience?: number;
    is_interested?: boolean;
    notes?: string;
  }): Promise<EmployeeSkill> => {
    const response = await api.put<EmployeeSkill>(`/api/user-skills/me/${id}`, data);
    return response.data;
  },
  update: async (id: number, data: {
    rating?: 'Beginner' | 'Developing' | 'Intermediate' | 'Advanced' | 'Expert';
    years_experience?: number;
    is_interested?: boolean;
    notes?: string;
  }): Promise<EmployeeSkill> => {
    const response = await api.put<EmployeeSkill>(`/api/user-skills/${id}`, data);
    return response.data;
  },
  deleteMySkill: async (id: number): Promise<void> => {
    await api.delete(`/api/user-skills/me/${id}`);
  },
};

// Search API
export const searchApi = {
  searchSkills: async (
    query: string,
    threshold: number = 75,
    limit: number = 50
  ): Promise<FuzzySearchResult[]> => {
    const response = await api.get<FuzzySearchResult[]>('/api/search/skills', {
      params: { q: query, threshold, limit },
    });
    return response.data;
  },
};

// Admin API
export const adminApi = {
  uploadSkills: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<UploadResponse>('/api/admin/upload-skills', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'X-ADMIN-KEY': 'dev-admin-key-change-in-production', // Dev only
      },
    });
    return response.data;
  },
  uploadEmployeeSkills: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<UploadResponse>('/api/admin/upload-employee-skills', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'X-ADMIN-KEY': 'dev-admin-key-change-in-production', // Dev only
      },
    });
    return response.data;
  },
  importUsers: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<UploadResponse>('/api/admin/import-users', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'X-ADMIN-KEY': 'dev-admin-key-change-in-production', // Dev only
      },
    });
    return response.data;
  },
  importEmployeeSkills: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<UploadResponse>('/api/admin/import-employee-skills', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'X-ADMIN-KEY': 'dev-admin-key-change-in-production', // Dev only
      },
    });
    return response.data;
  },
  importCategoryTemplates: async (file: File, category: string): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);
    const response = await api.post<UploadResponse>('/api/admin/import-category-templates', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// Admin Dashboard API
export interface EmployeeWithSkills extends Employee {
  skills?: EmployeeSkill[];
}

export interface SkillOverview {
  skill: Skill;
  total_employees: number;
  existing_skills_count: number;
  interested_skills_count: number;
  rating_breakdown: {
    Beginner: number;
    Developing: number;
    Intermediate: number;
    Advanced: number;
    Expert: number;
  };
}

export interface SkillImprovement {
  employee_id: string;
  employee_name: string;
  skill_name: string;
  initial_rating: string;
  current_rating: string;
  years_experience?: number;
}

export interface DashboardStats {
  total_employees: number;
  total_skills: number;
  total_skill_mappings: number;
  employees_with_existing_skills: number;
  employees_with_interested_skills: number;
  rating_breakdown: Record<string, number>;
}

// Bands API
export interface SkillGap {
  skill_id: number;
  employee_skill_id: number;
  skill_name: string;
  skill_category?: string;
  current_rating_text?: string;
  current_rating_number?: number;
  required_rating_text: string;
  required_rating_number: number;
  gap: number;
  is_required: boolean;
  notes?: string;
}

export interface BandAnalysis {
  employee_id: string;
  employee_name: string;
  band: string;
  average_rating: number;
  total_skills: number;
  skills_above_requirement: number;
  skills_at_requirement: number;
  skills_below_requirement: number;
  skill_gaps: SkillGap[];
}

// Categories API
export const categoriesApi = {
  getAll: async (): Promise<string[]> => {
    const response = await api.get<string[]>('/api/categories/');
    return response.data;
  },
  createCategory: async (categoryName: string): Promise<{ message: string; category: string }> => {
    const response = await api.post('/api/categories/create', null, {
      params: { category_name: categoryName }
    });
    return response.data;
  },
  getTemplate: async (category: string): Promise<any[]> => {
    const response = await api.get(`/api/categories/${category}/template`);
    return response.data;
  },
  getTemplateWithStats: async (category: string): Promise<any[]> => {
    const response = await api.get(`/api/categories/${category}/template-with-stats`);
    return response.data;
  },
  updateMandatoryStatus: async (category: string, templateId: number, isRequired: boolean): Promise<{ message: string; employees_updated?: number }> => {
    const response = await api.patch(`/api/categories/${category}/template/${templateId}/mandatory`, null, {
      params: { is_required: isRequired }
    });
    return response.data;
  },
  getSkillCategories: async (employeeCategory: string): Promise<string[]> => {
    const response = await api.get<string[]>(`/api/categories/${employeeCategory}/skill-categories`);
    return response.data;
  },
};

export const bandsApi = {
  getMyAnalysis: async (): Promise<BandAnalysis> => {
    const response = await api.get<BandAnalysis>('/api/bands/me/analysis');
    return response.data;
  },
  getAllEmployeesAnalysis: async (): Promise<BandAnalysis[]> => {
    const response = await api.get<BandAnalysis[]>('/api/bands/all/analysis');
    return response.data;
  },
  getEmployeeAnalysis: async (employeeId: string): Promise<BandAnalysis> => {
    const response = await api.get<BandAnalysis>(`/api/bands/employee/${employeeId}/analysis`);
    return response.data;
  },
};

// Learning Platform API
export interface Course {
  id: number;
  title: string;
  description?: string;
  skill_id?: number;
  skill_name?: string;
  external_url?: string;
  is_mandatory: boolean;
  created_at: string;
}

export interface CourseAssignment {
  id: number;
  course_id: number;
  course_title: string;
  course_external_url?: string;
  employee_id: number;
  employee_name: string;
  assigned_at: string;
  due_date?: string;
  status: 'Not Started' | 'In Progress' | 'Completed';
  started_at?: string;
  completed_at?: string;
  certificate_url?: string;
  notes?: string;
}

export const learningApi = {
  // Admin endpoints
  createCourse: async (course: {
    title: string;
    description?: string;
    skill_id?: number;
    external_url?: string;
    is_mandatory: boolean;
  }): Promise<Course> => {
    const response = await api.post<Course>('/api/learning/courses', course);
    return response.data;
  },
  
  getAllCourses: async (): Promise<Course[]> => {
    const response = await api.get<Course[]>('/api/learning/courses');
    return response.data;
  },
  
  assignCourse: async (assignment: {
    course_id: number;
    employee_ids: number[];
    due_date?: string;
  }): Promise<{ message: string; assigned: number; skipped: number }> => {
    const response = await api.post('/api/learning/assignments', assignment);
    return response.data;
  },
  
  getAllAssignments: async (): Promise<CourseAssignment[]> => {
    const response = await api.get<CourseAssignment[]>('/api/learning/assignments/all');
    return response.data;
  },
  
  deleteCourse: async (courseId: number): Promise<{ message: string }> => {
    const response = await api.delete(`/api/learning/courses/${courseId}`);
    return response.data;
  },
  
  // Employee endpoints
  getMyAssignments: async (): Promise<CourseAssignment[]> => {
    const response = await api.get<CourseAssignment[]>('/api/learning/my-assignments');
    return response.data;
  },
  
  startCourse: async (assignmentId: number): Promise<{ message: string }> => {
    const response = await api.patch(`/api/learning/assignments/${assignmentId}/start`);
    return response.data;
  },
  
  completeCourse: async (
    assignmentId: number,
    certificate?: File,
    notes?: string
  ): Promise<{ message: string; certificate_url?: string }> => {
    const formData = new FormData();
    if (certificate) {
      formData.append('certificate', certificate);
    }
    if (notes) {
      formData.append('notes', notes);
    }
    const response = await api.patch(`/api/learning/assignments/${assignmentId}/complete`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Auto-assignment endpoints
  autoAssignBySkillGap: async (): Promise<{
    message: string;
    assigned: number;
    skipped: number;
    details: Array<{
      employee_id: string;
      employee_name: string;
      course_title: string;
      skill_name: string;
      current_level: string;
      required_level: string;
    }>;
  }> => {
    const response = await api.post('/api/learning/auto-assign-by-skill-gap');
    return response.data;
  },

  autoAssignForEmployee: async (employeeId: number): Promise<{
    message: string;
    assigned: number;
    skipped: number;
    details: Array<{
      course_title: string;
      skill_name: string;
      current_level: string;
      required_level: string;
    }>;
  }> => {
    const response = await api.post(`/api/learning/auto-assign-for-employee/${employeeId}`);
    return response.data;
  },

  getSkillGapReport: async (): Promise<Array<{
    employee_id: number;
    employee_name: string;
    band: string;
    skill_gaps: Array<{
      skill_id: number;
      skill_name: string;
      current_level: string;
      required_level: string;
      assigned_courses: Array<{
        course_id: number;
        course_title: string;
        status: string;
      }>;
      available_courses: Array<{
        course_id: number;
        course_title: string;
      }>;
    }>;
  }>> => {
    const response = await api.get('/api/learning/skill-gap-report');
    return response.data;
  },
};

// Role Requirements API (Career Pathways)
export interface RoleRequirement {
  id: number;
  band: string;
  skill_id: number;
  skill_name: string;
  required_rating: string;
  is_required: boolean;
}

export interface PathwaySkill {
  skill_id: number;
  skill_name: string;
  skill_category?: string;
  band_requirements: Record<string, string>; // band -> required_rating
}

export const roleRequirementsApi = {
  getAll: async (band?: string, skillId?: number): Promise<RoleRequirement[]> => {
    const params: any = {};
    if (band) params.band = band;
    if (skillId) params.skill_id = skillId;
    const response = await api.get<RoleRequirement[]>('/api/role-requirements', { params });
    return response.data;
  },

  create: async (data: {
    band: string;
    skill_id: number;
    required_rating: string;
    is_required?: boolean;
  }): Promise<RoleRequirement> => {
    const response = await api.post<RoleRequirement>('/api/role-requirements', data);
    return response.data;
  },

  update: async (id: number, data: {
    band: string;
    skill_id: number;
    required_rating: string;
    is_required?: boolean;
  }): Promise<RoleRequirement> => {
    const response = await api.put<RoleRequirement>(`/api/role-requirements/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/role-requirements/${id}`);
  },

  // Get all pathways grouped by category
  getPathways: async (): Promise<Record<string, PathwaySkill[]>> => {
    const response = await api.get<Record<string, PathwaySkill[]>>('/api/role-requirements/pathways');
    return response.data;
  },

  // Bulk update requirements for a skill across all bands
  bulkUpdateSkill: async (skillId: number, bandRequirements: Record<string, string>): Promise<{ message: string; created: number; updated: number; deleted: number }> => {
    const response = await api.post(`/api/role-requirements/bulk-update/${skillId}`, { band_requirements: bandRequirements });
    return response.data;
  },

  // Add a skill to pathways with default requirements
  addSkillToPathway: async (skillId: number): Promise<{ message: string; skill_id: number; skill_name: string }> => {
    const response = await api.post('/api/role-requirements/add-skill', null, { params: { skill_id: skillId } });
    return response.data;
  },

  // Remove a skill from pathways
  removeSkillFromPathway: async (skillId: number): Promise<{ message: string; deleted_requirements: number }> => {
    const response = await api.delete(`/api/role-requirements/remove-skill/${skillId}`);
    return response.data;
  },

  // Add ALL skills to pathways with default requirements
  addAllSkillsToPathways: async (pathway?: string): Promise<{ message: string; added: number; skipped: number; added_skills: Array<{ skill_id: number; skill_name: string; category: string }>; pathway?: string }> => {
    const params = pathway ? { pathway } : {};
    const response = await api.post('/api/role-requirements/add-all-skills', null, { params });
    return response.data;
  },

  // Get list of available pathways with skill counts
  getPathwaysList: async (): Promise<Array<{ pathway: string; total_skills: number; skills_in_requirements: number; skills_remaining: number; skill_categories: string[] }>> => {
    const response = await api.get('/api/role-requirements/pathways-list');
    return response.data;
  },

  // Get skills for a specific pathway grouped by skill category
  getPathwaySkills: async (pathwayName: string): Promise<Record<string, PathwaySkill[]>> => {
    const response = await api.get(`/api/role-requirements/pathway/${encodeURIComponent(pathwayName)}/skills`);
    return response.data;
  },
};

export const adminDashboardApi = {
  getEmployees: async (skip: number = 0, limit: number = 100, department?: string): Promise<Employee[]> => {
    const params: any = { skip, limit };
    if (department) params.department = department;
    const response = await api.get<Employee[]>('/api/admin/employees', { params });
    return response.data;
  },
  getEmployeeSkills: async (employeeId: string): Promise<EmployeeSkill[]> => {
    const response = await api.get<EmployeeSkill[]>(`/api/admin/employees/${employeeId}/skills`);
    return response.data;
  },
  getSkillsOverview: async (category?: string, skillCategory?: string): Promise<SkillOverview[]> => {
    const params: any = {};
    if (category) params.category = category;
    if (skillCategory) params.skill_category = skillCategory;
    const response = await api.get<SkillOverview[]>('/api/admin/skills/overview', { params });
    return response.data;
  },
  getSkillImprovements: async (skillId?: number, employeeId?: string, days: number = 30): Promise<{
    improvements: SkillImprovement[];
    total_count: number;
    note: string;
  }> => {
    const params: any = { days };
    if (skillId) params.skill_id = skillId;
    if (employeeId) params.employee_id = employeeId;
    const response = await api.get('/api/admin/skill-improvements', { params });
    return response.data;
  },
  getDashboardStats: async (): Promise<DashboardStats> => {
    const response = await api.get<DashboardStats>('/api/admin/dashboard/stats');
    return response.data;
  },
  searchEmployeesBySkill: async (criteria: Array<{skill_name: string, rating?: string}>): Promise<{
    total_results: number;
    employees: Array<{
      employee: Employee;
      matching_skills: Array<{
        skill_id: number;
        skill_name: string;
        skill_category?: string;
        rating: string | null;
        years_experience?: number;
        match_score?: number;
        criterion_index?: number;
      }>;
      match_count: number;
      criteria_count: number;
      match_percentage: number;
    }>;
  }> => {
    const response = await api.post('/api/admin/employees/search', { criteria });
    return response.data;
  },
};

