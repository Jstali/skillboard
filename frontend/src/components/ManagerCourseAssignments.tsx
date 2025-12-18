/**
 * Manager Course Assignments Component
 * 
 * Displays all course assignments made by the current manager.
 * Supports filtering by status, employee, and course.
 * 
 * Requirements: 5.1, 5.2, 5.3
 */
import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { BookOpen, User, Calendar, Filter, RefreshCw, ExternalLink, CheckCircle, Clock, AlertCircle } from 'lucide-react';

interface CourseAssignment {
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

interface ManagerCourseAssignmentsProps {
  compact?: boolean; // For dashboard summary view
  maxItems?: number; // Limit items in compact mode
}

export const ManagerCourseAssignments: React.FC<ManagerCourseAssignmentsProps> = ({
  compact = false,
  maxItems
}) => {
  const [assignments, setAssignments] = useState<CourseAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filter state
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [employeeFilter, setEmployeeFilter] = useState<string>('');
  const [courseFilter, setCourseFilter] = useState<string>('');
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    loadAssignments();
  }, [statusFilter]);

  const loadAssignments = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params: Record<string, string> = {};
      if (statusFilter) params.status_filter = statusFilter;
      
      const response = await api.get('/api/courses/assignments/manager', { params });
      setAssignments(response.data);
    } catch (err: any) {
      console.error('Failed to load assignments:', err);
      setError(err.response?.data?.detail || 'Failed to load course assignments');
    } finally {
      setLoading(false);
    }
  };


  // Get unique employees and courses for filter dropdowns
  const uniqueEmployees = [...new Set(assignments.map(a => a.employee_name))].sort();
  const uniqueCourses = [...new Set(assignments.map(a => a.course_title))].sort();

  // Apply client-side filters for employee and course
  const filteredAssignments = assignments.filter(a => {
    if (employeeFilter && a.employee_name !== employeeFilter) return false;
    if (courseFilter && a.course_title !== courseFilter) return false;
    return true;
  });

  // Limit items in compact mode
  const displayAssignments = maxItems 
    ? filteredAssignments.slice(0, maxItems) 
    : filteredAssignments;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'In Progress':
        return <Clock className="w-4 h-4 text-blue-600" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'Completed':
        return 'bg-green-100 text-green-800';
      case 'In Progress':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString();
  };

  const isOverdue = (dueDate?: string, status?: string) => {
    if (!dueDate || status === 'Completed') return false;
    return new Date(dueDate) < new Date();
  };

  // Stats summary
  const stats = {
    total: assignments.length,
    notStarted: assignments.filter(a => a.status === 'Not Started').length,
    inProgress: assignments.filter(a => a.status === 'In Progress').length,
    completed: assignments.filter(a => a.status === 'Completed').length,
    overdue: assignments.filter(a => isOverdue(a.due_date, a.status)).length
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Loading assignments...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-600">{error}</p>
        <button
          onClick={loadAssignments}
          className="mt-2 px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  // Compact view for dashboard
  if (compact) {
    return (
      <div className="space-y-3">
        {/* Quick Stats */}
        <div className="grid grid-cols-4 gap-2 text-center">
          <div className="p-2 bg-gray-50 rounded">
            <p className="text-lg font-bold text-gray-800">{stats.total}</p>
            <p className="text-xs text-gray-500">Total</p>
          </div>
          <div className="p-2 bg-yellow-50 rounded">
            <p className="text-lg font-bold text-yellow-700">{stats.notStarted}</p>
            <p className="text-xs text-yellow-600">Not Started</p>
          </div>
          <div className="p-2 bg-blue-50 rounded">
            <p className="text-lg font-bold text-blue-700">{stats.inProgress}</p>
            <p className="text-xs text-blue-600">In Progress</p>
          </div>
          <div className="p-2 bg-green-50 rounded">
            <p className="text-lg font-bold text-green-700">{stats.completed}</p>
            <p className="text-xs text-green-600">Completed</p>
          </div>
        </div>

        {/* Recent Assignments */}
        {displayAssignments.length === 0 ? (
          <p className="text-gray-500 text-sm text-center py-4">No course assignments yet</p>
        ) : (
          <div className="space-y-2">
            {displayAssignments.map(assignment => (
              <div key={assignment.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <div className="flex items-center gap-2">
                  {getStatusIcon(assignment.status)}
                  <div>
                    <p className="text-sm font-medium">{assignment.course_title}</p>
                    <p className="text-xs text-gray-500">{assignment.employee_name}</p>
                  </div>
                </div>
                <span className={`px-2 py-0.5 text-xs rounded ${getStatusBadgeClass(assignment.status)}`}>
                  {assignment.status}
                </span>
              </div>
            ))}
          </div>
        )}

        {filteredAssignments.length > (maxItems || 0) && (
          <p className="text-xs text-gray-500 text-center">
            +{filteredAssignments.length - (maxItems || 0)} more assignments
          </p>
        )}
      </div>
    );
  }


  // Full view
  return (
    <div className="space-y-4">
      {/* Header with Stats */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h3 className="text-lg font-semibold text-gray-800">Course Assignments</h3>
          <div className="flex gap-2 text-sm">
            <span className="px-2 py-1 bg-gray-100 rounded">{stats.total} Total</span>
            {stats.overdue > 0 && (
              <span className="px-2 py-1 bg-red-100 text-red-700 rounded">{stats.overdue} Overdue</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-1 px-3 py-1.5 text-sm rounded ${
              showFilters ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'
            }`}
          >
            <Filter className="w-4 h-4" />
            Filters
          </button>
          <button
            onClick={loadAssignments}
            className="flex items-center gap-1 px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="p-4 bg-gray-50 rounded-lg border">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Statuses</option>
                <option value="Not Started">Not Started</option>
                <option value="In Progress">In Progress</option>
                <option value="Completed">Completed</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Employee</label>
              <select
                value={employeeFilter}
                onChange={(e) => setEmployeeFilter(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Employees</option>
                {uniqueEmployees.map(emp => (
                  <option key={emp} value={emp}>{emp}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Course</label>
              <select
                value={courseFilter}
                onChange={(e) => setCourseFilter(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Courses</option>
                {uniqueCourses.map(course => (
                  <option key={course} value={course}>{course}</option>
                ))}
              </select>
            </div>
          </div>
          {(statusFilter || employeeFilter || courseFilter) && (
            <button
              onClick={() => {
                setStatusFilter('');
                setEmployeeFilter('');
                setCourseFilter('');
              }}
              className="mt-3 text-sm text-blue-600 hover:text-blue-800"
            >
              Clear all filters
            </button>
          )}
        </div>
      )}

      {/* Assignments Table */}
      {filteredAssignments.length === 0 ? (
        <div className="p-8 text-center bg-white rounded-lg border">
          <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No course assignments found</p>
          {(statusFilter || employeeFilter || courseFilter) && (
            <p className="text-sm text-gray-400 mt-1">Try adjusting your filters</p>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-lg border overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Course</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Employee</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Assigned</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Due Date</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Skill Gap</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filteredAssignments.map(assignment => (
                <tr key={assignment.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <BookOpen className="w-4 h-4 text-gray-400" />
                      <div>
                        <p className="text-sm font-medium text-gray-800">{assignment.course_title}</p>
                        {assignment.course_description && (
                          <p className="text-xs text-gray-500 truncate max-w-xs">{assignment.course_description}</p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4 text-gray-400" />
                      <span className="text-sm">{assignment.employee_name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1 text-sm text-gray-600">
                      <Calendar className="w-4 h-4" />
                      {formatDate(assignment.assigned_at)}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-sm ${isOverdue(assignment.due_date, assignment.status) ? 'text-red-600 font-medium' : 'text-gray-600'}`}>
                      {formatDate(assignment.due_date)}
                      {isOverdue(assignment.due_date, assignment.status) && ' (Overdue)'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded ${getStatusBadgeClass(assignment.status)}`}>
                      {getStatusIcon(assignment.status)}
                      {assignment.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {assignment.skill_name ? (
                      <span className="text-sm text-purple-600">{assignment.skill_name}</span>
                    ) : (
                      <span className="text-sm text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {assignment.course_url && (
                      <a
                        href={assignment.course_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
                      >
                        <ExternalLink className="w-4 h-4" />
                        View
                      </a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Notes Section */}
      {filteredAssignments.some(a => a.notes) && (
        <div className="mt-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
          <h4 className="text-sm font-medium text-yellow-800 mb-2">Assignment Notes</h4>
          <div className="space-y-2">
            {filteredAssignments.filter(a => a.notes).map(a => (
              <div key={a.id} className="text-sm">
                <span className="font-medium">{a.employee_name} - {a.course_title}:</span>
                <span className="text-gray-600 ml-2">{a.notes}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ManagerCourseAssignments;
