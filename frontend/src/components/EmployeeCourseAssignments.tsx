/**
 * Employee Course Assignments Component
 * 
 * Displays courses assigned to the current employee.
 * Shows course details, assigner, dates, and status.
 * Allows employees to start courses and mark them as complete.
 * 
 * Requirements: 6.1, 6.2, 6.3, 6.4
 */
import React, { useState, useEffect } from 'react';
import { coursesApi, CourseAssignmentDetails } from '../services/api';
import { 
  BookOpen, 
  User, 
  Calendar, 
  RefreshCw, 
  ExternalLink, 
  CheckCircle, 
  Clock, 
  AlertCircle,
  Play,
  Award,
  Upload,
  X
} from 'lucide-react';

interface EmployeeCourseAssignmentsProps {
  compact?: boolean; // For dashboard summary view
  maxItems?: number; // Limit items in compact mode
  onRefresh?: () => void; // Callback after status update
}

export const EmployeeCourseAssignments: React.FC<EmployeeCourseAssignmentsProps> = ({
  compact = false,
  maxItems,
  onRefresh
}) => {
  const [assignments, setAssignments] = useState<CourseAssignmentDetails[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  
  // Certificate upload modal state
  const [showCertificateModal, setShowCertificateModal] = useState(false);
  const [selectedAssignment, setSelectedAssignment] = useState<CourseAssignmentDetails | null>(null);
  const [certificateUrl, setCertificateUrl] = useState('');

  useEffect(() => {
    loadAssignments();
  }, []);

  const loadAssignments = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await coursesApi.getMyAssignments();
      setAssignments(data);
    } catch (err: any) {
      console.error('Failed to load assignments:', err);
      setError(err.response?.data?.detail || 'Failed to load course assignments');
    } finally {
      setLoading(false);
    }
  };


  const handleStartCourse = async (assignmentId: number) => {
    try {
      setUpdatingId(assignmentId);
      await coursesApi.updateAssignmentStatus(assignmentId, 'In Progress');
      await loadAssignments();
      onRefresh?.();
    } catch (err: any) {
      console.error('Failed to start course:', err);
      alert(err.response?.data?.detail || 'Failed to start course');
    } finally {
      setUpdatingId(null);
    }
  };

  const handleCompleteCourse = async () => {
    if (!selectedAssignment) return;
    
    try {
      setUpdatingId(selectedAssignment.id);
      await coursesApi.updateAssignmentStatus(
        selectedAssignment.id, 
        'Completed',
        certificateUrl || undefined
      );
      await loadAssignments();
      onRefresh?.();
      setShowCertificateModal(false);
      setSelectedAssignment(null);
      setCertificateUrl('');
    } catch (err: any) {
      console.error('Failed to complete course:', err);
      alert(err.response?.data?.detail || 'Failed to complete course');
    } finally {
      setUpdatingId(null);
    }
  };

  const openCompletionModal = (assignment: CourseAssignmentDetails) => {
    setSelectedAssignment(assignment);
    setCertificateUrl('');
    setShowCertificateModal(true);
  };

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

  // Sort assignments: Not Started first, then In Progress, then Completed
  const sortedAssignments = [...assignments].sort((a, b) => {
    const statusOrder: Record<string, number> = {
      'Not Started': 0,
      'In Progress': 1,
      'Completed': 2
    };
    return (statusOrder[a.status] || 0) - (statusOrder[b.status] || 0);
  });

  // Stats summary
  const stats = {
    total: assignments.length,
    notStarted: assignments.filter(a => a.status === 'Not Started').length,
    inProgress: assignments.filter(a => a.status === 'In Progress').length,
    completed: assignments.filter(a => a.status === 'Completed').length,
    overdue: assignments.filter(a => isOverdue(a.due_date, a.status)).length
  };

  // Limit items in compact mode
  const displayAssignments = maxItems 
    ? sortedAssignments.slice(0, maxItems) 
    : sortedAssignments;

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Loading your courses...</span>
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
            <p className="text-xs text-yellow-600">Pending</p>
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

        {/* Pending/In Progress Courses */}
        {displayAssignments.length === 0 ? (
          <p className="text-gray-500 text-sm text-center py-4">No courses assigned yet</p>
        ) : (
          <div className="space-y-2">
            {displayAssignments.map(assignment => (
              <div key={assignment.id} className="p-3 bg-gray-50 rounded-lg border border-gray-100">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start gap-2 flex-1 min-w-0">
                    {getStatusIcon(assignment.status)}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{assignment.course_title}</p>
                      <p className="text-xs text-gray-500">
                        Assigned by {assignment.assigner_name || 'Manager'}
                      </p>
                      {assignment.due_date && (
                        <p className={`text-xs mt-1 ${isOverdue(assignment.due_date, assignment.status) ? 'text-red-600 font-medium' : 'text-gray-500'}`}>
                          Due: {formatDate(assignment.due_date)}
                          {isOverdue(assignment.due_date, assignment.status) && ' (Overdue)'}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className={`px-2 py-0.5 text-xs rounded ${getStatusBadgeClass(assignment.status)}`}>
                      {assignment.status}
                    </span>
                    {assignment.status === 'Not Started' && (
                      <button
                        onClick={() => handleStartCourse(assignment.id)}
                        disabled={updatingId === assignment.id}
                        className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                      >
                        {updatingId === assignment.id ? '...' : 'Start'}
                      </button>
                    )}
                    {assignment.status === 'In Progress' && (
                      <button
                        onClick={() => openCompletionModal(assignment)}
                        disabled={updatingId === assignment.id}
                        className="px-2 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                      >
                        Complete
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {sortedAssignments.length > (maxItems || 0) && (
          <p className="text-xs text-gray-500 text-center">
            +{sortedAssignments.length - (maxItems || 0)} more courses
          </p>
        )}

        {/* Certificate Upload Modal */}
        {showCertificateModal && selectedAssignment && (
          <CertificateModal
            assignment={selectedAssignment}
            certificateUrl={certificateUrl}
            setCertificateUrl={setCertificateUrl}
            onComplete={handleCompleteCourse}
            onClose={() => {
              setShowCertificateModal(false);
              setSelectedAssignment(null);
              setCertificateUrl('');
            }}
            isUpdating={updatingId === selectedAssignment.id}
          />
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
          <h3 className="text-lg font-semibold text-gray-800">My Courses</h3>
          <div className="flex gap-2 text-sm">
            <span className="px-2 py-1 bg-gray-100 rounded">{stats.total} Total</span>
            {stats.overdue > 0 && (
              <span className="px-2 py-1 bg-red-100 text-red-700 rounded">{stats.overdue} Overdue</span>
            )}
          </div>
        </div>
        <button
          onClick={loadAssignments}
          className="flex items-center gap-1 px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="p-4 bg-white rounded-lg border shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gray-100 rounded-lg">
              <BookOpen className="w-5 h-5 text-gray-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-800">{stats.total}</p>
              <p className="text-sm text-gray-500">Total Courses</p>
            </div>
          </div>
        </div>
        <div className="p-4 bg-white rounded-lg border shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <AlertCircle className="w-5 h-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-yellow-700">{stats.notStarted}</p>
              <p className="text-sm text-gray-500">Not Started</p>
            </div>
          </div>
        </div>
        <div className="p-4 bg-white rounded-lg border shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Clock className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-700">{stats.inProgress}</p>
              <p className="text-sm text-gray-500">In Progress</p>
            </div>
          </div>
        </div>
        <div className="p-4 bg-white rounded-lg border shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-green-700">{stats.completed}</p>
              <p className="text-sm text-gray-500">Completed</p>
            </div>
          </div>
        </div>
      </div>

      {/* Courses List */}
      {sortedAssignments.length === 0 ? (
        <div className="p-8 text-center bg-white rounded-lg border">
          <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No courses assigned to you yet</p>
          <p className="text-sm text-gray-400 mt-1">Your manager will assign courses based on your skill gaps</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg border overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Course</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Assigned By</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Assigned Date</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Due Date</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Skill</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {sortedAssignments.map(assignment => (
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
                      <span className="text-sm">{assignment.assigner_name || 'Manager'}</span>
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
                    {assignment.status === 'Completed' && assignment.completed_at && (
                      <p className="text-xs text-gray-500 mt-1">
                        {formatDate(assignment.completed_at)}
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {assignment.skill_name ? (
                      <span className="text-sm text-purple-600">{assignment.skill_name}</span>
                    ) : (
                      <span className="text-sm text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
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
                      {assignment.status === 'Not Started' && (
                        <button
                          onClick={() => handleStartCourse(assignment.id)}
                          disabled={updatingId === assignment.id}
                          className="inline-flex items-center gap-1 px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                        >
                          <Play className="w-3 h-3" />
                          {updatingId === assignment.id ? 'Starting...' : 'Start'}
                        </button>
                      )}
                      {assignment.status === 'In Progress' && (
                        <button
                          onClick={() => openCompletionModal(assignment)}
                          disabled={updatingId === assignment.id}
                          className="inline-flex items-center gap-1 px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                        >
                          <Award className="w-3 h-3" />
                          Complete
                        </button>
                      )}
                      {assignment.status === 'Completed' && assignment.certificate_url && (
                        <a
                          href={assignment.certificate_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-sm text-green-600 hover:text-green-800"
                        >
                          <Award className="w-4 h-4" />
                          Certificate
                        </a>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Notes Section */}
      {sortedAssignments.some(a => a.notes) && (
        <div className="mt-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
          <h4 className="text-sm font-medium text-yellow-800 mb-2">Manager Notes</h4>
          <div className="space-y-2">
            {sortedAssignments.filter(a => a.notes).map(a => (
              <div key={a.id} className="text-sm">
                <span className="font-medium">{a.course_title}:</span>
                <span className="text-gray-600 ml-2">{a.notes}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Certificate Upload Modal */}
      {showCertificateModal && selectedAssignment && (
        <CertificateModal
          assignment={selectedAssignment}
          certificateUrl={certificateUrl}
          setCertificateUrl={setCertificateUrl}
          onComplete={handleCompleteCourse}
          onClose={() => {
            setShowCertificateModal(false);
            setSelectedAssignment(null);
            setCertificateUrl('');
          }}
          isUpdating={updatingId === selectedAssignment.id}
        />
      )}
    </div>
  );
};


// Certificate Upload Modal Component
interface CertificateModalProps {
  assignment: CourseAssignmentDetails;
  certificateUrl: string;
  setCertificateUrl: (url: string) => void;
  onComplete: () => void;
  onClose: () => void;
  isUpdating: boolean;
}

const CertificateModal: React.FC<CertificateModalProps> = ({
  assignment,
  certificateUrl,
  setCertificateUrl,
  onComplete,
  onClose,
  isUpdating
}) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">Complete Course</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>
        
        <div className="mb-4">
          <p className="text-sm text-gray-600">
            Mark <span className="font-medium">{assignment.course_title}</span> as completed.
          </p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Certificate URL (Optional)
            </label>
            <div className="flex items-center gap-2">
              <Upload className="w-4 h-4 text-gray-400" />
              <input
                type="url"
                value={certificateUrl}
                onChange={(e) => setCertificateUrl(e.target.value)}
                placeholder="https://certificate-link.com"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Add a link to your certificate if you have one
            </p>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              onClick={onComplete}
              disabled={isUpdating}
              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 font-medium flex items-center justify-center gap-2"
            >
              {isUpdating ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Completing...
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4" />
                  Mark as Complete
                </>
              )}
            </button>
            <button
              onClick={onClose}
              disabled={isUpdating}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 font-medium"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmployeeCourseAssignments;
