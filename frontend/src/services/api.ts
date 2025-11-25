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
}

export interface EmployeeSkill {
  id: number;
  employee_id: number;
  skill_id: number;
  rating?: 'Beginner' | 'Developing' | 'Intermediate' | 'Advanced' | 'Expert' | null;  // Optional for interested skills
  years_experience?: number;
  is_interested?: boolean;
  notes?: string;
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
  getById: async (id: number): Promise<Skill> => {
    const response = await api.get<Skill>(`/api/skills/${id}`);
    return response.data;
  },
  create: async (skill: { name: string; description?: string }): Promise<Skill> => {
    const response = await api.post<Skill>('/api/skills/', skill);
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
    rating?: 'Beginner' | 'Developing' | 'Intermediate' | 'Advanced' | 'Expert';  // Optional for interested skills
    years_experience?: number;
    is_interested?: boolean;
    notes?: string;
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
  skill_name: string;
  skill_category?: string;
  current_rating_text?: string;
  current_rating_number?: number;
  required_rating_text: string;
  required_rating_number: number;
  gap: number;
  is_required: boolean;
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
  getTemplate: async (category: string): Promise<any[]> => {
    const response = await api.get(`/api/categories/${category}/template`);
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

