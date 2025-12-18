/** API service for backend communication. */
import axios from 'axios';

// Use relative path to leverage Vite proxy, or fallback to env variable
// In development with Vite proxy, use empty string (relative paths)
// In production or when proxy is not available, use full URL
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 second timeout
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



export interface User {
  id: number;
  email: string;
  employee_id?: string;
  is_active: boolean;
  is_admin: boolean;
  must_change_password: boolean;
  created_at: string;
  role_id?: number;  // 1=admin, 2=hr, 3=cp, 4=dm, 5=lm, 6=employee
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
  create: async (skill: { name: string; description?: string; category?: string; pathway?: string }, addToCategory?: string): Promise<Skill> => {
    const params = addToCategory ? { add_to_category: addToCategory } : {};
    const response = await api.post<Skill>('/api/skills/', skill, { params });
    return response.data;
  },
  // Get skills grouped by pathway and category
  getGrouped: async (): Promise<Record<string, Record<string, Skill[]>>> => {
    const response = await api.get<Record<string, Record<string, Skill[]>>>('/api/skills/grouped');
    return response.data;
  },
  // Get list of pathways with categories and counts
  getPathways: async (): Promise<Array<{ name: string; categories: Record<string, number>; total_skills: number }>> => {
    const response = await api.get('/api/skills/pathways');
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
export interface EmployeeSkill {
  id: number;
  employee_id: number;
  skill_id: number;
  rating: string | null; // e.g., "Intermediate"
  years_experience: number | null;
  is_interested: boolean;
  notes?: string;
  is_custom: boolean;
  learning_status: string; // Not Started, Learning, Stuck, Completed
  status_updated_at: string;
  employee?: {
    id: number;
    employee_id: string;
    name: string;
  };
  skill?: Skill; // Joined skill details
}

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
    learning_status?: string;
  }): Promise<EmployeeSkill> => {
    const response = await api.put<EmployeeSkill>(`/api/user-skills/me/${id}`, data);
    return response.data;
  },
  update: async (id: number, data: {
    rating?: 'Beginner' | 'Developing' | 'Intermediate' | 'Advanced' | 'Expert';
    years_experience?: number;
    is_interested?: boolean;
    notes?: string;
    learning_status?: string;
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

// HR Dashboard API
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
export interface SuggestedCourse {
  id: number;
  title: string;
  external_url?: string;
  is_mandatory: boolean;
}

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
  requirement_source: string;
  learning_status: string;
  pending_days: number;
  suggested_courses?: SuggestedCourse[];
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
  // Get band analysis for current user
  getMyAnalysis: async (targetBand?: string): Promise<BandAnalysis> => {
    const params = targetBand ? { target_band: targetBand } : {};
    const response = await api.get<BandAnalysis>('/api/bands/me/analysis', { params });
    return response.data;
  },
  getAllEmployeesAnalysis: async (): Promise<BandAnalysis[]> => {
    const response = await api.get<BandAnalysis[]>('/api/bands/all/analysis');
    return response.data;
  },
  // Get band analysis for a specific employee
  getEmployeeAnalysis: async (employeeId: string, targetBand?: string): Promise<BandAnalysis> => {
    const params = targetBand ? { target_band: targetBand } : {};
    const response = await api.get<BandAnalysis>(`/api/bands/employee/${employeeId}/analysis`, { params });
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
  addSkillToPathway: async (skillId: number, category?: string): Promise<{ message: string; skill_id: number; skill_name: string }> => {
    const params: any = { skill_id: skillId };
    if (category) params.category = category;
    const response = await api.post('/api/role-requirements/add-skill', null, { params });
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
  searchEmployeesBySkill: async (criteria: Array<{ skill_name: string, rating?: string }>): Promise<{
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


// Templates API
export interface SkillTemplate {
  id: number;
  template_name: string;
  file_name: string;
  created_at: string;
  row_count?: number;
  content?: string[][];
}

export interface TemplateUploadResponse {
  message: string;
  templates_created?: number;
  template_names?: string[];
  rows_processed?: number;
  rows_created?: number;
  rows_updated?: number;
  errors?: string[];
}

export const templatesApi = {
  upload: async (file: File, templateName?: string): Promise<TemplateUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (templateName) {
      formData.append('template_name', templateName);
    }
    // Must set Content-Type to multipart/form-data for file uploads
    const response = await api.post<TemplateUploadResponse>('/api/admin/templates/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getAll: async (): Promise<SkillTemplate[]> => {
    const response = await api.get<SkillTemplate[]>('/api/admin/templates');
    return response.data;
  },

  getById: async (id: number): Promise<SkillTemplate> => {
    const response = await api.get<SkillTemplate>(`/api/admin/templates/${id}`);
    return response.data;
  },

  update: async (id: number, content: any[][]): Promise<SkillTemplate> => {
    const response = await api.put<SkillTemplate>(`/api/admin/templates/${id}`, { content });
    return response.data;
  },

  rename: async (id: number, newName: string): Promise<SkillTemplate> => {
    const response = await api.put<SkillTemplate>(`/api/admin/templates/${id}/rename`, { new_name: newName });
    return response.data;
  },

  getDropdown: async (): Promise<{ id: number; name: string }[]> => {
    const response = await api.get<{ id: number; name: string }[]>('/api/admin/templates/options/dropdown');
    return response.data;
  },

  assign: async (templateId: number, employeeIds: number[], filters?: { department?: string, role?: string, team?: string }): Promise<{ message: string; errors: string[] }> => {
    const response = await api.post<{ message: string; errors: string[] }>('/api/admin/templates/assign', {
      template_id: templateId,
      employee_ids: employeeIds,
      ...filters
    });
    return response.data;
  },

  delete: async (id: number): Promise<{ message: string }> => {
    const response = await api.delete<{ message: string }>(`/api/admin/templates/${id}`);
    return response.data;
  },

  getSample: async (): Promise<{ template_name: string; content: any[][] }[]> => {
    const response = await api.get<{ template_name: string; content: any[][] }[]>('/api/admin/templates/sample');
    return response.data;
  },
};

// Employee Assignments API
export interface AssignedTemplate {
  id: number;
  template_name: string;
  assigned_at: string;
  status: string; // "Pending", "In Progress", "Completed"
}

export interface TemplateSkill {
  id: number;
  name: string;
  category?: string;
  description?: string;
}

export interface AssignmentDetails {
  id: number;
  template: {
    id: number;
    name: string;
    skills: TemplateSkill[];
  };
  status: string;
  assigned_at: string;
}

export interface SkillResponseData {
  skill_id: number;
  level?: string; // Beginner, Developing, Intermediate, Advanced, Expert
  years_experience?: number;
  notes?: string;
}

export interface SubmitTemplateData {
  employee_category: string;
  responses: SkillResponseData[];
}

export const employeeAssignmentsApi = {
  getMyAssignments: async (): Promise<AssignedTemplate[]> => {
    const response = await api.get<{ pending: AssignedTemplate[]; completed: AssignedTemplate[] }>('/api/employee/assignments/my-assignments');
    // Combine pending and completed into a single array
    return [...(response.data.pending || []), ...(response.data.completed || [])];
  },

  getAssignmentDetails: async (assignmentId: number): Promise<AssignmentDetails> => {
    const response = await api.get<AssignmentDetails>(`/api/employee/assignments/${assignmentId}`);
    return response.data;
  },

  submitTemplate: async (assignmentId: number, data: SubmitTemplateData): Promise<{ message: string }> => {
    const response = await api.post(`/api/employee/assignments/${assignmentId}/submit`, data);
    return response.data;
  },
};


// ============================================================================
// HRMS PRE-INTEGRATION TYPES & APIs
// ============================================================================

// Project types
export interface Project {
  id: number;
  name: string;
  description?: string;
  capability_required?: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  capability_required?: string;
}

export interface EmployeeProjectAssignment {
  id: number;
  employee_id: number;
  project_id: number;
  is_primary: boolean;
  percentage_allocation?: number;
  line_manager_id?: number;
  capability_owner_id?: number;
  start_date?: string;
  end_date?: string;
  created_at: string;
  updated_at: string;
}

export interface AssignEmployeeToProject {
  employee_id: number;
  project_id: number;
  is_primary?: boolean;
  percentage_allocation?: number;
  line_manager_id?: number;
  capability_owner_id?: number;
  start_date?: string;
  end_date?: string;
}

// Capability Owner types
export interface CapabilityOwner {
  id: number;
  capability_name: string;
  owner_employee_id?: number;
  created_at: string;
}

export interface CapabilityOwnerCreate {
  capability_name: string;
  owner_employee_id?: number;
}

// Level Movement types
export interface LevelMovementRequest {
  id: number;
  employee_id: number;
  current_level?: string;
  requested_level: string;
  status: string;
  readiness_score?: number;
  submission_date: string;
  manager_approval_date?: string;
  cp_approval_date?: string;
  hr_approval_date?: string;
  rejection_reason?: string;
}

export interface LevelMovementRequestCreate {
  requested_level: string;
}

export interface ApprovalRequest {
  comments?: string;
}

// Org Structure types
export interface OrgStructure {
  id: number;
  employee_id: number;
  manager_id?: number;
  level?: number;
  created_at: string;
  updated_at: string;
}

// Projects API
export const projectsApi = {
  list: async (): Promise<Project[]> => {
    const response = await api.get<Project[]>('/api/projects');
    return response.data;
  },

  get: async (id: number): Promise<Project> => {
    const response = await api.get<Project>(`/api/projects/${id}`);
    return response.data;
  },

  create: async (data: ProjectCreate): Promise<Project> => {
    const response = await api.post<Project>('/api/projects', data);
    return response.data;
  },

  update: async (id: number, data: Partial<ProjectCreate>): Promise<Project> => {
    const response = await api.put<Project>(`/api/projects/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/projects/${id}`);
  },

  assignEmployee: async (projectId: number, data: AssignEmployeeToProject): Promise<EmployeeProjectAssignment> => {
    const response = await api.post<EmployeeProjectAssignment>(`/api/projects/${projectId}/assign-employee`, data);
    return response.data;
  },

  getEmployeeProjects: async (employeeId: number): Promise<EmployeeProjectAssignment[]> => {
    const response = await api.get<EmployeeProjectAssignment[]>(`/api/projects/employee/${employeeId}/projects`);
    return response.data;
  },

  updateAssignment: async (assignmentId: number, data: Partial<AssignEmployeeToProject>): Promise<EmployeeProjectAssignment> => {
    const response = await api.put<EmployeeProjectAssignment>(`/api/projects/assignments/${assignmentId}`, data);
    return response.data;
  },

  deleteAssignment: async (assignmentId: number): Promise<void> => {
    await api.delete(`/api/projects/assignments/${assignmentId}`);
  },
};

// Capability Owners API
export const capabilityOwnersApi = {
  list: async (): Promise<CapabilityOwner[]> => {
    const response = await api.get<CapabilityOwner[]>('/api/capability-owners');
    return response.data;
  },

  get: async (id: number): Promise<CapabilityOwner> => {
    const response = await api.get<CapabilityOwner>(`/api/capability-owners/${id}`);
    return response.data;
  },

  create: async (data: CapabilityOwnerCreate): Promise<CapabilityOwner> => {
    const response = await api.post<CapabilityOwner>('/api/capability-owners', data);
    return response.data;
  },

  update: async (id: number, data: CapabilityOwnerCreate): Promise<CapabilityOwner> => {
    const response = await api.put<CapabilityOwner>(`/api/capability-owners/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/capability-owners/${id}`);
  },

  getEmployees: async (id: number): Promise<Employee[]> => {
    const response = await api.get<Employee[]>(`/api/capability-owners/${id}/employees`);
    return response.data;
  },
};

// Org Structure API
export const orgStructureApi = {
  assignManager: async (employeeId: number, managerId: number): Promise<{ message: string }> => {
    const response = await api.post('/api/org-structure/assign-manager', null, {
      params: { employee_id: employeeId, manager_id: managerId }
    });
    return response.data;
  },

  uploadStructure: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<UploadResponse>('/api/org-structure/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  getStructure: async (): Promise<OrgStructure[]> => {
    const response = await api.get<OrgStructure[]>('/api/org-structure');
    return response.data;
  },

  getDirectReports: async (employeeId: number): Promise<Employee[]> => {
    const response = await api.get<Employee[]>(`/api/org-structure/employees/${employeeId}/direct-reports`);
    return response.data;
  },

  getHierarchy: async (employeeId: number): Promise<any> => {
    const response = await api.get(`/api/org-structure/employees/${employeeId}/hierarchy`);
    return response.data;
  },
};

// Level Movement API
export const levelMovementApi = {
  createRequest: async (data: LevelMovementRequestCreate): Promise<LevelMovementRequest> => {
    const response = await api.post<LevelMovementRequest>('/api/level-movement/request', data);
    return response.data;
  },

  listRequests: async (statusFilter?: string): Promise<LevelMovementRequest[]> => {
    const response = await api.get<LevelMovementRequest[]>('/api/level-movement/requests', {
      params: statusFilter ? { status_filter: statusFilter } : {}
    });
    return response.data;
  },

  getRequest: async (id: number): Promise<LevelMovementRequest> => {
    const response = await api.get<LevelMovementRequest>(`/api/level-movement/requests/${id}`);
    return response.data;
  },

  getMyRequests: async (): Promise<LevelMovementRequest[]> => {
    const response = await api.get<LevelMovementRequest[]>('/api/level-movement/my-requests');
    return response.data;
  },

  getPendingApprovals: async (): Promise<LevelMovementRequest[]> => {
    const response = await api.get<LevelMovementRequest[]>('/api/level-movement/pending-approvals');
    return response.data;
  },

  approve: async (id: number, data: ApprovalRequest): Promise<LevelMovementRequest> => {
    const response = await api.post<LevelMovementRequest>(`/api/level-movement/requests/${id}/approve`, data);
    return response.data;
  },

  reject: async (id: number, data: ApprovalRequest): Promise<LevelMovementRequest> => {
    const response = await api.post<LevelMovementRequest>(`/api/level-movement/requests/${id}/reject`, data);
    return response.data;
  },

  getApprovals: async (id: number): Promise<any[]> => {
    const response = await api.get(`/api/level-movement/requests/${id}/approvals`);
    return response.data;
  },
};

// ============================================================================
// SKILL BOARD VIEWS TYPES & APIs
// ============================================================================

// Skill Board Types
export interface ProficiencyDisplay {
  level: string;
  color: string;
  icon: string;
  numeric_value: number;
  description: string;
  css_class: string;
}

export interface SkillWithProficiency {
  skill_id: number;
  skill_name: string;
  category?: string;
  rating?: string;
  rating_display: ProficiencyDisplay;
  years_experience?: number;
  is_required: boolean;
  meets_requirement: boolean;
}

export interface SkillGapInfo {
  skill_id: number;
  skill_name: string;
  category?: string;
  required_level: string;
  actual_level?: string;
  gap_value: number;
  priority: string;
}

export interface CapabilityAlignmentInfo {
  capability: string;
  alignment_score: number;
  required_skills_met: number;
  required_skills_total: number;
  average_proficiency: number;
}

export interface EmployeeSkillBoardData {
  employee_id: string;
  name: string;
  home_capability?: string;
  team?: string;
  skills: SkillWithProficiency[];
  capability_alignment?: CapabilityAlignmentInfo;
  skill_gaps: SkillGapInfo[];
}

// Metrics Types
export interface SkillDistribution {
  capability?: string;
  total_employees: number;
  skill_counts: Record<string, number>;
  proficiency_distribution: Record<string, Record<string, number>>;
}

export interface CoverageMetrics {
  capability: string;
  coverage_percentage: number;
  skills_with_coverage: number;
  skills_without_coverage: number;
  critical_gaps: string[];
}

export interface TrainingNeedInfo {
  skill_name: string;
  current_coverage: number;
  required_coverage: number;
  gap_percentage: number;
  priority: string;
}

// Reconciliation Types
export interface AssignmentInfoData {
  project_name: string;
  allocation_percentage?: number;
  is_primary: boolean;
  start_date?: string;
  end_date?: string;
}

export interface DiscrepancyInfo {
  employee_id: string;
  employee_name: string;
  discrepancy_type: string;
  skill_board_value?: string;
  hrms_value?: string;
  field: string;
}

export interface ReconciliationResultData {
  employee_id: string;
  employee_name: string;
  skill_board_assignments: AssignmentInfoData[];
  hrms_assignments: AssignmentInfoData[];
  discrepancies: DiscrepancyInfo[];
  match_status: string;
}

export interface ReconciliationReportData {
  generated_at: string;
  total_employees: number;
  employees_matched: number;
  employees_with_discrepancies: number;
  total_discrepancies: number;
  discrepancy_breakdown: Record<string, number>;
  results: ReconciliationResultData[];
}

// Skill Board API
export const skillBoardApi = {
  getEmployeeSkillBoard: async (employeeId: string): Promise<EmployeeSkillBoardData> => {
    const response = await api.get<EmployeeSkillBoardData>(`/api/skill-board/${employeeId}`);
    return response.data;
  },

  getEmployeeSkills: async (employeeId: string): Promise<SkillWithProficiency[]> => {
    const response = await api.get<SkillWithProficiency[]>(`/api/skill-board/${employeeId}/skills`);
    return response.data;
  },

  getEmployeeGaps: async (employeeId: string): Promise<SkillGapInfo[]> => {
    const response = await api.get<SkillGapInfo[]>(`/api/skill-board/${employeeId}/gaps`);
    return response.data;
  },

  getEmployeeAlignment: async (employeeId: string): Promise<CapabilityAlignmentInfo | null> => {
    const response = await api.get<CapabilityAlignmentInfo | null>(`/api/skill-board/${employeeId}/alignment`);
    return response.data;
  },
};

// Metrics API
export const metricsApi = {
  getSkillCountsByProficiency: async (
    capability?: string,
    team?: string,
    band?: string
  ): Promise<Record<string, number>> => {
    const params: any = {};
    if (capability) params.capability = capability;
    if (team) params.team = team;
    if (band) params.band = band;
    const response = await api.get<Record<string, number>>('/api/metrics/counts', { params });
    return response.data;
  },

  getCapabilityDistribution: async (capability?: string): Promise<SkillDistribution> => {
    const params = capability ? { capability } : {};
    const response = await api.get<SkillDistribution>('/api/metrics/distribution', { params });
    return response.data;
  },

  getCapabilityCoverage: async (capability: string): Promise<CoverageMetrics> => {
    const response = await api.get<CoverageMetrics>(`/api/metrics/coverage/${capability}`);
    return response.data;
  },

  getTrainingNeeds: async (capability: string): Promise<TrainingNeedInfo[]> => {
    const response = await api.get<TrainingNeedInfo[]>(`/api/metrics/training-needs/${capability}`);
    return response.data;
  },
};

// Reconciliation API
export const reconciliationApi = {
  compareEmployeeAssignments: async (employeeId: string): Promise<ReconciliationResultData> => {
    const response = await api.get<ReconciliationResultData>(`/api/reconciliation/compare/${employeeId}`);
    return response.data;
  },

  getAllDiscrepancies: async (): Promise<DiscrepancyInfo[]> => {
    const response = await api.get<DiscrepancyInfo[]>('/api/reconciliation/discrepancies');
    return response.data;
  },

  getReconciliationReport: async (): Promise<ReconciliationReportData> => {
    const response = await api.get<ReconciliationReportData>('/api/reconciliation/report');
    return response.data;
  },

  exportReconciliationData: async (format: string = 'json'): Promise<Blob> => {
    const response = await api.get('/api/reconciliation/export', {
      params: { format },
      responseType: 'blob'
    });
    return response.data;
  },
};


// ============================================================================
// TEMPLATE ASSESSMENT TYPES & APIs (Manager-Driven)
// ============================================================================

// Template Assessment Types
export interface TemplateListItem {
  id: number;
  template_name: string;
  file_name: string;
  created_at: string;
  skill_count: number;
}

export interface TemplateSkillView {
  skill_id: number;
  skill_name: string;
  skill_category?: string;
  required_level?: string;
  current_level?: string;
  is_assessed: boolean;
}

export interface TemplateAssessmentView {
  template_id: number;
  template_name: string;
  employee_id: number;
  employee_name: string;
  skills: TemplateSkillView[];
  total_skills: number;
  assessed_skills: number;
}

export interface SkillAssessmentInput {
  skill_id: number;
  level: string;
  comments?: string;
}

export interface TemplateAssessmentResult {
  template_id: number;
  employee_id: number;
  assessor_id: number;
  skills_assessed: number;
  total_skills: number;
  log_id: number;
  assessed_at: string;
}

export interface AssessmentProgress {
  template_id: number;
  employee_id: number;
  total_skills: number;
  assessed_skills: number;
  completion_percentage: number;
}

export interface AssessableEmployee {
  id: number;
  employee_id: string;
  name: string;
  band?: string;
  pathway?: string;
  department?: string;
}

// Template Assessment API
export const templateAssessmentApi = {
  // Get list of available templates for assessment
  getTemplates: async (): Promise<TemplateListItem[]> => {
    const response = await api.get<TemplateListItem[]>('/api/assessments/templates');
    return response.data;
  },

  // Get assessable employees for the current manager
  getAssessableEmployees: async (): Promise<AssessableEmployee[]> => {
    const response = await api.get<AssessableEmployee[]>('/api/assessments/assessable-employees');
    return response.data;
  },

  // Get template skills with employee's current levels
  getTemplateForAssessment: async (templateId: number, employeeId: number): Promise<TemplateAssessmentView> => {
    const response = await api.get<TemplateAssessmentView>(
      `/api/assessments/template/${templateId}/employee/${employeeId}`
    );
    return response.data;
  },

  // Submit template assessments
  submitTemplateAssessment: async (
    templateId: number,
    employeeId: number,
    assessments: SkillAssessmentInput[]
  ): Promise<TemplateAssessmentResult> => {
    const response = await api.post<TemplateAssessmentResult>(
      `/api/assessments/template/${templateId}/employee/${employeeId}`,
      { assessments }
    );
    return response.data;
  },

  // Get assessment progress for a template/employee
  getAssessmentProgress: async (templateId: number, employeeId: number): Promise<AssessmentProgress> => {
    const response = await api.get<AssessmentProgress>(
      `/api/assessments/template/${templateId}/employee/${employeeId}/progress`
    );
    return response.data;
  },
};


// ============================================================================
// COURSE ASSIGNMENT TYPES & APIs (Manager-Driven)
// ============================================================================

// Course Assignment Types
export interface CourseDetails {
  id: number;
  title: string;
  description?: string;
  skill_id?: number;
  skill_name?: string;
  external_url?: string;
  is_mandatory: boolean;
  created_at?: string;
}

export interface CourseAssignmentDetails {
  id: number;
  course_id: number;
  course_title: string;
  course_description?: string;
  course_url?: string;
  employee_id: number;
  employee_name: string;
  assigned_by?: number;
  assigner_name?: string;
  assigned_at: string;
  due_date?: string;
  status: string;
  started_at?: string;
  completed_at?: string;
  certificate_url?: string;
  notes?: string;
  skill_id?: number;
  skill_name?: string;
}

export interface CourseAssignRequest {
  course_id: number;
  employee_id: number;
  due_date?: string;
  notes?: string;
  skill_id?: number;
}

// Course Assignment API
export const coursesApi = {
  // Get all courses with optional filtering
  getCourses: async (params?: {
    skill_id?: number;
    mandatory?: boolean;
    search?: string;
  }): Promise<CourseDetails[]> => {
    const response = await api.get<CourseDetails[]>('/api/courses', { params });
    return response.data;
  },

  // Get courses for a specific skill
  getCoursesForSkill: async (skillId: number): Promise<CourseDetails[]> => {
    const response = await api.get<CourseDetails[]>(`/api/courses/skill/${skillId}`);
    return response.data;
  },

  // Assign a course to an employee
  assignCourse: async (request: CourseAssignRequest): Promise<CourseAssignmentDetails> => {
    const response = await api.post<CourseAssignmentDetails>('/api/courses/assign', request);
    return response.data;
  },

  // Get assignments made by the current manager
  getManagerAssignments: async (params?: {
    status_filter?: string;
    employee_id?: number;
    course_id?: number;
  }): Promise<CourseAssignmentDetails[]> => {
    const response = await api.get<CourseAssignmentDetails[]>('/api/courses/assignments/manager', { params });
    return response.data;
  },

  // Get assignments for the current employee
  getMyAssignments: async (): Promise<CourseAssignmentDetails[]> => {
    const response = await api.get<CourseAssignmentDetails[]>('/api/courses/assignments/me');
    return response.data;
  },

  // Update assignment status
  updateAssignmentStatus: async (
    assignmentId: number,
    status: string,
    certificateUrl?: string
  ): Promise<CourseAssignmentDetails> => {
    const response = await api.put<CourseAssignmentDetails>(
      `/api/courses/assignments/${assignmentId}/status`,
      { status, certificate_url: certificateUrl }
    );
    return response.data;
  },
};
